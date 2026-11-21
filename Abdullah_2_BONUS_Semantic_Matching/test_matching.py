"""Matching (AI feature 2): embeddings, factors, scores, explanations, hard rules, fallback, decisions, screens."""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.ai.models import AICapability, AIInferenceRecord, AIOutcome, ModelStatus, ModelVersion
from apps.catalogue.models import Asset, Category
from apps.common.enums import Condition, Urgency, UserDecision
from apps.common.errors import Forbidden, ValidationFailed
from apps.matching import services
from apps.notifications.models import Notification
from apps.matching.embeddings import LexicalEmbedder, concepts_in, cosine, normalise, tokens
from apps.matching.engine import (DEFAULT_WEIGHTS, HIGH_URGENCY_WEIGHTS, Candidate, MatchingEngine, Need, guess_quantity,
                                  score)
from apps.matching.models import EmbeddingIndex, MatchRecommendation, MatchResultSet, ResultSetStatus
from apps.resource_requests import services as req_services
from apps.resource_requests.models import ResourceRequest
from apps.sustainability.models import EmissionFactor

from .factories import World


class EmbeddingTests(SimpleTestCase):
    def setUp(self):
        self.e = LexicalEmbedder()

    def sim(self, a, b):
        x, y = self.e.embed([a, b])
        return cosine(x, y)

    def test_arabic_is_normalised(self):
        self.assertEqual(normalise("الشّاشة"), "الشاشه")
        self.assertEqual(tokens("للطاولات والكراسي"), ["طاولات", "كراسي"])
        self.assertEqual(concepts_in("شاشتين"), {"monitor"})

    def test_vectors_are_unit_length_and_384_wide(self):
        v = self.e.embed(["a monitor"])[0]
        self.assertEqual(len(v), 384)
        self.assertAlmostEqual(sum(x * x for x in v), 1.0, places=6)

    def test_meaning_beats_spelling(self):
        self.assertGreater(self.sim("display screen", "Dell monitor"), self.sim("display screen", "office chair"))
        self.assertGreater(self.sim("شاشة عرض", "Dell 24-inch monitor"), self.sim("شاشة عرض", "bookshelf"))
        self.assertGreater(self.sim("seats for a seminar", "stackable stool"), self.sim("seats for a seminar", "oscilloscope"))

    def test_quantity_is_read_from_words_but_sizes_are_not(self):
        self.assertEqual(guess_quantity("Two 24-inch monitors"), 2)
        self.assertEqual(guess_quantity("need 3 scopes"), 3)
        self.assertIsNone(guess_quantity("a 27 inch screen"))
        self.assertEqual(guess_quantity("شاشتان مقاس 24 بوصة"), 2)


class ScoreTests(SimpleTestCase):
    def test_weights_add_up_to_one(self):
        self.assertAlmostEqual(sum(DEFAULT_WEIGHTS.values()), 1.0)
        self.assertAlmostEqual(sum(HIGH_URGENCY_WEIGHTS.values()), 1.0)

    def test_score_is_weighted_sum_out_of_100(self):
        s, pts = score({k: 1.0 for k in DEFAULT_WEIGHTS}, DEFAULT_WEIGHTS)
        self.assertEqual(s, 100)
        s, pts = score({"f1": 0.5}, DEFAULT_WEIGHTS)
        self.assertEqual((s, pts["f1"]), (15, 15))

    def test_rank_drops_weak_and_explains_from_contributions(self):
        a1, a2, a3 = (mock.Mock(estimated_value=Decimal(100), name=n) for n in "abc")
        full = {k: 1.0 for k in DEFAULT_WEIGHTS}
        low = {k: 0.3 for k in DEFAULT_WEIGHTS}
        out = MatchingEngine().rank([Candidate(a2, {**full, "f5": 0.5}), Candidate(a1, full), Candidate(a3, low)], Urgency.MEDIUM)
        self.assertEqual([r.asset for r in out], [a1, a2])  # a3 scores 30: hidden
        self.assertTrue(out[0].explanation.startswith("Good fit: similar purpose, specifications met"))

    def test_neutral_inputs_are_not_claimed_as_reasons(self):
        a = mock.Mock(estimated_value=None)
        c = Candidate(a, {k: 1.0 for k in DEFAULT_WEIGHTS} | {"f2": 0.7}, neutral={"f2"})
        _, pts = score(c.factors, DEFAULT_WEIGHTS)
        self.assertNotIn("specifications", MatchingEngine().explain(c, pts))


class FactorTests(TestCase):
    def setUp(self):
        self.w = World(qty=4)
        self.engine = MatchingEngine("lexical")

    def f(self, **need):
        n = Need(text="monitor for a workstation", campus="Main", building="B1", **need)
        return self.engine.factors(n, self.w.asset, 0.6, None)

    def test_location(self):
        self.assertEqual(self.f().factors["f4"], 1.0)
        self.w.asset.location_building = "B9"
        self.assertEqual(self.f().factors["f4"], 0.8)
        self.w.asset.location_campus = "SAN"
        c = self.f()
        self.assertEqual(c.factors["f4"], 0.4)
        self.assertIn("other campus (SAN)", c.notes)

    def test_condition(self):
        self.assertEqual(self.f(preferred_condition="GOOD").factors["f3"], 1.0)
        self.assertEqual(self.f(preferred_condition="NEW").factors["f3"], 0.5)
        self.w.asset.condition = Condition.POOR
        c = self.f(preferred_condition="NEW")
        self.assertEqual(c.factors["f3"], 0.0)
        self.assertEqual(c.factors["f5"], 0.5)  # needs repair first

    def test_specs_and_size(self):
        self.w.asset.specifications = "24 in, HDMI"
        self.assertEqual(self.f(specs="HDMI").factors["f2"], 1.0)
        c = self.f(specs="27 inch HDMI")
        self.assertLess(c.factors["f2"], 0.5)
        self.assertIn("different size", c.notes)

    def test_cost_and_unknown_value(self):
        c = self.f(quantity=2)  # move 40 against 2 x 650
        self.assertAlmostEqual(c.factors["f6"], round(1 - 40 / 1300, 3))
        self.w.asset.estimated_value = None
        c = self.f()
        self.assertEqual(c.factors["f6"], 0.5)
        self.assertIn("f6", c.neutral)

    def test_tight_date(self):
        self.assertLess(self.f(required_date=date.today() + timedelta(days=1)).factors["f5"], 1)
        self.assertEqual(self.f(required_date=date.today() + timedelta(days=30)).factors["f5"], 1)

    def test_unrelated_item_is_not_a_candidate(self):
        self.assertIsNone(self.engine.factors(Need(text="x"), self.w.asset, 0.05, None))


class FlowTests(TestCase):
    def setUp(self):
        self.w = World(qty=4)
        w = self.w
        mk = lambda name, cat, dept, **kw: Asset.objects.create(  # noqa: E731
            name=name, category=cat, owner_department=dept, custodian=w.custodian, quantity=kw.pop("q", 2),
            available_quantity=kw.pop("q2", 2), condition=Condition.GOOD, estimated_value=Decimal("400"),
            location_campus="Main", location_building="B1", **kw)
        self.chairs = Category.objects.create(name="Chairs", name_ar="كراسي")
        self.chair = mk("Office chair", self.chairs, w.cs, specifications="armrests")
        self.own = mk("ME monitor", w.category, w.me)  # the requester's own unit: never suggested
        for a in (self.chair, self.own):
            a.mark_available(w.custodian)
            a.publish(w.custodian)
        self.hidden = mk("Unpublished monitor", w.category, w.cs)
        w.asset.specifications = "24 in, HDMI"
        w.asset.save()
        w.me.campus = "Main"
        w.me.save()

    def test_find_ranks_explains_and_logs(self):
        out = services.find("a 24 inch monitor for our lab", self.w.requester)
        names = [r.asset.name for r in out.suitable + out.weak]
        self.assertEqual(names[0], "Dell monitor")
        self.assertNotIn("ME monitor", names)
        self.assertNotIn("Unpublished monitor", names)
        self.assertNotIn("Office chair", names)
        top = out.suitable[0]
        self.assertGreaterEqual(top.compatibility_score, 70)
        self.assertEqual(set(top.factor_scores["factors"]), set(DEFAULT_WEIGHTS))
        self.assertTrue(top.explanation)
        rs = out.result_set
        self.assertIsNone(rs.request)
        self.assertEqual(rs.model_version.capability, AICapability.RANK)
        self.assertEqual(rs.model_version.config["weights"], DEFAULT_WEIGHTS)
        self.assertTrue(AIInferenceRecord.objects.filter(capability=AICapability.RANK, outcome=AIOutcome.OK).exists())
        self.assertEqual(EmbeddingIndex.objects.filter(object_id=self.w.asset.pk).count(), 1)

    def test_arabic_query_finds_english_item(self):
        out = services.find("كرسي مكتب", self.w.requester)
        self.assertEqual([r.asset.name for r in out.suitable], ["Office chair"])

    def test_not_enough_free_units_is_a_hard_rule(self):
        out = services.find("monitor", self.w.requester, quantity=5)
        self.assertFalse(out.suitable + out.weak)

    def test_nothing_relevant(self):
        out = services.find("banana", self.w.requester)
        self.assertTrue(out.ranked)
        self.assertFalse(out.suitable + out.weak)
        self.assertTrue(AIInferenceRecord.objects.filter(outcome=AIOutcome.NO_EVIDENCE).exists())

    def test_fallback_when_matching_is_unavailable(self):
        with mock.patch("apps.matching.services.get_embedder", side_effect=RuntimeError("model missing")):
            out = services.find("Dell monitor", self.w.requester)
        self.assertFalse(out.ranked)
        self.assertEqual([a.name for a in out.fallback], ["Dell monitor"])
        self.assertTrue(AIInferenceRecord.objects.filter(outcome=AIOutcome.UNAVAILABLE).exists())

    def test_embeddings_are_reused_until_the_text_changes(self):
        mv = services.embed_model()
        self.assertGreater(services.ensure_asset_embeddings([self.w.asset], mv), 0)
        self.assertEqual(services.ensure_asset_embeddings([self.w.asset], mv), 0)
        self.w.asset.update({"description": "Matte screen"}, self.w.custodian)
        self.assertEqual(services.ensure_asset_embeddings([self.w.asset], mv), 1)

    def test_one_active_model_per_capability_and_a_new_row_when_settings_change(self):
        a = services.rank_model()
        self.assertEqual(services.rank_model().pk, a.pk)
        with mock.patch("apps.matching.services.DEFAULT_WEIGHTS", {**DEFAULT_WEIGHTS, "f1": 0.31}):
            b = services.rank_model()
        self.assertNotEqual(a.pk, b.pk)
        self.assertEqual(ModelVersion.objects.filter(capability=AICapability.RANK, status=ModelStatus.ACTIVE).count(), 1)

    def test_carbon_factor_from_a_parent_category(self):
        parent = Category.objects.create(name="IT")
        self.w.category.parent = parent
        self.w.category.save()
        EmissionFactor.objects.create(category=parent, kg_co2e_per_unit=Decimal("250"), source="Local study", source_date=date(2025, 1, 1))
        out = services.find("monitor", self.w.requester)
        self.assertEqual(out.suitable[0].factor_scores["factors"]["f7"], 1.0)


class RequestSuggestionTests(TestCase):
    def setUp(self):
        self.w = World(qty=4)
        self.req, _ = req_services.submit_request(self.w.requester, {
            "department": self.w.me, "category": self.w.category, "quantity": 2, "purpose": "Two monitors for a lab bench",
            "destination_campus": "Main", "destination_building": "B2"}, uuid.uuid4().hex)

    def test_generate_supersedes_and_reuses_current(self):
        first = services.generate_matches(self.req.pk, self.w.requester).result_set
        again = services.suggestions_for(self.req, self.w.requester).result_set
        self.assertEqual(first.pk, again.pk)  # nothing changed: same result set
        self.w.asset.update({"specifications": "27 in"}, self.w.custodian)  # row_version changes the snapshot
        third = services.suggestions_for(self.req, self.w.requester).result_set
        self.assertNotEqual(third.pk, first.pk)
        first.refresh_from_db()
        self.assertEqual(first.status, ResultSetStatus.SUPERSEDED)

    def test_choose_selects_item_and_records_acceptance(self):
        rec = services.generate_matches(self.req.pk, self.w.requester).suitable[0]
        req = services.choose_for_request(rec.pk, self.w.requester)
        self.assertEqual(req.selected_asset_id, self.w.asset.pk)
        rec.refresh_from_db()
        self.assertEqual(rec.user_decision, UserDecision.ACCEPTED)
        self.assertTrue(Notification.objects.filter(recipient=self.w.approver, subject_ref=f"ResourceRequest:{req.pk}").exists())

    def test_only_the_requester_decides(self):
        rec = services.generate_matches(self.req.pk, self.w.requester).suitable[0]
        with self.assertRaises(Forbidden):
            services.choose_for_request(rec.pk, self.w.requester2)
        with self.assertRaises(Forbidden):
            services.record_decision(rec.pk, self.w.requester2, UserDecision.REJECTED, "too far away")

    def test_not_for_me_needs_reason_and_hides_the_item_next_time(self):
        rec = services.generate_matches(self.req.pk, self.w.requester).suitable[0]
        with self.assertRaises(ValidationFailed):
            services.record_decision(rec.pk, self.w.requester, UserDecision.REJECTED, "")
        services.record_decision(rec.pk, self.w.requester, UserDecision.REJECTED, "too far away")
        out = services.suggestions_for(self.req, self.w.requester)
        self.assertFalse(out.suitable + out.weak)


class ScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=4)
        self.client.force_login(self.w.requester)

    def test_find_page_and_partial(self):
        r = self.client.get(reverse("matching:find"))
        self.assertContains(r, "What do you need?")
        r = self.client.get(reverse("matching:find"), {"q": "Two monitors"}, HTTP_HX_REQUEST="true", HTTP_HX_TARGET="results")
        self.assertContains(r, "Dell monitor")
        self.assertContains(r, "Why this score")
        self.assertContains(r, "Looking for 2")
        self.assertNotContains(r, "<html")

    def test_request_from_a_match_counts_as_accepted(self):
        out = services.find("monitor", self.w.requester)
        rec = out.suitable[0]
        r = self.client.post(reverse("resource_requests:new"), {
            "asset": self.w.asset.pk, "match": rec.pk, "department": self.w.me.pk, "quantity": 1, "purpose": "Lab",
            "preferred_condition": "ANY", "urgency": "MEDIUM", "destination_campus": "Main", "idempotency_key": uuid.uuid4().hex})
        self.assertEqual(r.status_code, 302)
        rec.refresh_from_db()
        self.assertEqual(rec.user_decision, UserDecision.ACCEPTED)

    def test_not_for_me_and_choose_views(self):
        req, _ = req_services.submit_request(self.w.requester, {
            "department": self.w.me, "category": self.w.category, "quantity": 1, "purpose": "monitor",
            "destination_campus": "Main"}, uuid.uuid4().hex)
        r = self.client.get(reverse("matching:for_request", args=[req.pk]))
        self.assertContains(r, "Pick an item so this can be approved")
        rec = MatchRecommendation.objects.filter(result_set__request=req).first()
        r = self.client.post(reverse("matching:choose", args=[rec.pk]), HTTP_HX_REQUEST="true")
        self.assertIn("HX-Redirect", r.headers)
        self.assertEqual(ResourceRequest.objects.get(pk=req.pk).selected_asset_id, self.w.asset.pk)
        self.client.force_login(self.w.requester2)  # someone else's suggestion is a 404 (no leaking ids)
        self.assertEqual(self.client.post(reverse("matching:not_for_me", args=[rec.pk]), {"reason": "x"}).status_code, 404)

    def test_people_without_request_permission_cannot_open_find(self):
        self.client.force_login(self.w.custodian)
        self.assertEqual(self.client.get(reverse("matching:find")).status_code, 403)

    def test_result_sets_are_not_shared(self):
        services.find("monitor", self.w.requester)
        self.assertEqual(MatchResultSet.objects.filter(generated_by=self.w.requester).count(), 1)
