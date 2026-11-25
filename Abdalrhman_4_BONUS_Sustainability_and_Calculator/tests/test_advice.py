"""Feature 2: sustainable-action recommendations. Rule-based, read-only, linked to existing workflows."""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.ai.models import AICapability, AIOutcome, ModelVersion
from apps.ai.result import AIResult
from apps.catalogue import services as cat
from apps.catalogue.models import Asset, AssetState
from apps.common.enums import Condition, EndOfLifeAction
from apps.common.errors import Forbidden
from apps.lifecycle import services as lc
from apps.lifecycle.models import EndOfLifeProposal, LifeCycleEvent, MaintenanceRecord, MaintenanceType, RepairAction
from apps.resource_requests.models import ResourceRequest
from apps.sustainability import advice
from apps.sustainability.models import EmissionFactor

from .factories import World, role, user


class Gateway:
    """Stands in for AIGateway: returns a fixed result from a model version we control."""

    def __init__(self, text, provider="anthropic", status=AIOutcome.OK):
        self.mv = ModelVersion.objects.create(capability=AICapability.RECOMMEND, provider=provider, model_name="m-1", version="1")
        self.text, self.status = text, status

    def recommend_action(self, payload, user=None):
        self.payload = payload
        r = AIResult(self.status, value={"text": self.text} if self.text else None)
        r.model_version_id = self.mv.pk
        return r


class Base(TestCase):
    def setUp(self):
        self.w = World(qty=2)
        role("Custodian", "asset.register", "asset.publish", "asset.custody", "maintenance.record", "eol.propose")
        self.a = self.w.asset
        self.a.purchase_date = date(2023, 1, 1)
        self.a.save(update_fields=["purchase_date"])

    def rec(self, who=None):
        return advice.recommend(who or self.w.custodian, Asset.objects.get(pk=self.a.pk))

    def set(self, **kw):
        Asset.objects.filter(pk=self.a.pk).update(**kw)
        self.a.refresh_from_db()


class RuleTests(Base):
    def test_working_published_item_keep_it_listed(self):
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.RETAIN)
        self.assertIsNone(adv.recommended.link)
        self.assertTrue(adv.recommended.advice_only)

    def test_waiting_requests_elsewhere_suggest_transfer_and_link_to_publish(self):
        cat.unpublish(self.w.custodian, self.a)
        ResourceRequest.objects.create(requester=self.w.requester, department=self.w.me, category=self.w.category, purpose="Lab",
                                       quantity=2, destination_campus="Main", idempotency_key="adv-1")
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.TRANSFER)
        self.assertIn("1 request(s) for 2 unit(s)", " ".join(adv.recommended.why))
        self.assertEqual(adv.recommended.link.url.split("?")[0], reverse("catalogue:mine"))

    def test_poor_item_worth_repairing(self):
        cat.unpublish(self.w.custodian, self.a)
        self.set(condition=Condition.POOR)
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.REPAIR)
        self.assertEqual(adv.recommended.link.url, reverse("lifecycle:report", args=[self.a.pk]))
        self.assertIn("AED 130", [e.value for e in adv.estimates])  # 20 % of AED 650, the shared assumption

    def test_repeated_failed_repairs_suggest_recycling_with_disassembly_as_advice_only(self):
        cat.unpublish(self.w.custodian, self.a)
        rec = MaintenanceRecord.objects.create(asset=self.a, opened_by=self.w.custodian, record_type=MaintenanceType.DEFECT,
                                               description="dead", current_condition=Condition.POOR)
        for _i in range(2):
            RepairAction.objects.create(maintenance=rec, technician=self.w.custodian, description="try", outcome="UNSUCCESSFUL", cost=Decimal("50"))
        self.set(condition=Condition.POOR)
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.RECYCLE)
        self.assertIn("action=RECYCLE", adv.recommended.link.url)
        dis = next(o for o in adv.alternatives if o.action == EndOfLifeAction.DISASSEMBLE)
        self.assertIsNone(dis.link)
        self.assertIn("no disassembly workflow", dis.advice_only)
        self.assertEqual(adv.alternatives[-1].action, EndOfLifeAction.DISPOSE)  # last option, always last

    def test_expensive_repairs_so_far_stop_repairing(self):
        cat.unpublish(self.w.custodian, self.a)
        rec = MaintenanceRecord.objects.create(asset=self.a, opened_by=self.w.custodian, record_type=MaintenanceType.DEFECT,
                                               description="x", current_condition=Condition.FAIR)
        RepairAction.objects.create(maintenance=rec, technician=self.w.custodian, description="big", outcome="SUCCESSFUL", cost=Decimal("400"))
        adv = self.rec()  # 400 > half of 650
        self.assertEqual(adv.recommended.action, EndOfLifeAction.RECYCLE)

    def test_reserved_units_mean_let_the_transfer_finish(self):
        self.set(reserved_quantity=1)
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.RETAIN)
        self.assertEqual(adv.alternatives, [])

    def test_retired_in_good_condition_donate(self):
        self.set(lifecycle_state=AssetState.RETIRED, publication_status="UNPUBLISHED")
        adv = self.rec()
        self.assertEqual(adv.recommended.action, EndOfLifeAction.DONATE)
        self.assertIn("action=DONATE", adv.recommended.link.url)

    def test_open_proposal_is_respected(self):
        cat.unpublish(self.w.custodian, self.a)
        EndOfLifeProposal.objects.create(asset=self.a, proposed_by=self.w.custodian, action_type="DONATE", reason="old")
        adv = self.rec()
        self.assertEqual(adv.recommended.action, "DONATE")
        self.assertIn("already", adv.recommended.why[0])
        self.assertEqual(adv.alternatives, [])

    def test_ended_life_cycle_has_no_recommendation(self):
        self.set(lifecycle_state=AssetState.RECYCLED, publication_status="UNPUBLISHED")
        adv = self.rec()
        self.assertTrue(adv.ended)
        self.assertIsNone(adv.recommended)

    def test_missing_value_is_named_not_invented(self):
        self.set(estimated_value=None, purchase_date=None)
        adv = self.rec()
        text = " ".join(adv.facts.missing)
        self.assertIn("Estimated value", text)
        self.assertIn("Purchase date", text)
        self.assertIn("Carbon factor", text)
        self.assertFalse(any("AED" in e.value for e in adv.estimates))

    def test_carbon_estimate_cites_the_locally_selected_factor(self):
        EmissionFactor.objects.create(category=self.w.category, kg_co2e_per_unit=Decimal("300"), source="Test factor",
                                      source_date=date(2026, 1, 1))
        adv = self.rec()
        carbon = next(e for e in adv.estimates if "CO2e" in e.value)
        self.assertIn("Locally selected carbon factor: Test factor", carbon.how)

    def test_no_button_for_a_step_the_role_cannot_start(self):
        sara = user("Sara", self.w.uni, (role("Sustainability", "sustainability.review"), None))
        self.set(lifecycle_state=AssetState.RETIRED, publication_status="UNPUBLISHED")
        adv = advice.recommend(sara, Asset.objects.get(pk=self.a.pk))
        self.assertIsNone(adv.recommended.link)
        self.assertIn("Ask the unit's custodian", adv.recommended.advice_only)


class ReadOnlyAndAccessTests(Base):
    def test_viewing_changes_nothing(self):
        before = (self.a.row_version, LifeCycleEvent.objects.count(), EndOfLifeProposal.objects.count())
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("sustainability:advice", args=[self.a.pk]), HTTP_HX_REQUEST="true")
        self.assertContains(r, "Rule-based")
        self.a.refresh_from_db()
        self.assertEqual(before, (self.a.row_version, LifeCycleEvent.objects.count(), EndOfLifeProposal.objects.count()))

    def test_requesters_cannot_open_it(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("sustainability:advice", args=[self.a.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("sustainability:advice_ai", args=[self.a.pk])).status_code, 404)
        with self.assertRaises(Forbidden):
            advice.explain_with_ai(self.w.requester, self.a)

    def test_green_button_in_the_panel_for_custodians_only(self):
        url = reverse("catalogue:panel", args=[self.a.pk])
        self.client.force_login(self.w.custodian)
        r = self.client.get(url)
        self.assertContains(r, "btn btn-green")
        self.assertContains(r, "Sustainable actions")
        self.assertContains(r, reverse("sustainability:advice", args=[self.a.pk]))
        self.client.force_login(self.w.requester)
        self.assertNotContains(self.client.get(url), "Sustainable actions")

    def test_full_page_works_without_htmx(self):
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("sustainability:advice", args=[self.a.pk]))
        self.assertContains(r, "Recommended next step")

    def test_arabic(self):
        self.client.force_login(self.w.custodian)
        self.client.post(reverse("set_language"), {"language": "ar", "next": "/"})
        r = self.client.get(reverse("sustainability:advice", args=[self.a.pk]))
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "الخطوة التالية المقترحة")

    def test_propose_form_preselects_the_suggested_action(self):
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("lifecycle:propose", args=[self.a.pk]) + "?action=DONATE", HTTP_HX_REQUEST="true")
        self.assertContains(r, '<option value="DONATE" selected>')


class AiWordingTests(Base):
    def test_fake_provider_falls_back_to_the_rules(self):
        self.client.force_login(self.w.custodian)
        r = self.client.post(reverse("sustainability:advice_ai", args=[self.a.pk]))
        self.assertContains(r, "rule-based explanation above stands")

    def test_real_model_text_is_labelled(self):
        out = advice.explain_with_ai(self.w.custodian, self.a, gateway=Gateway("Keep it listed so others can reuse it."))
        self.assertTrue(out["ok"])
        self.assertTrue(out["real"])
        self.assertEqual(out["model"], "m-1")

    def test_offline_stand_in_is_not_called_a_real_model(self):
        out = advice.explain_with_ai(self.w.custodian, self.a, gateway=Gateway("Keep it listed.", provider="fake"))
        self.assertTrue(out["ok"])
        self.assertFalse(out["real"])

    def test_invented_numbers_are_discarded(self):
        out = advice.explain_with_ai(self.w.custodian, self.a, gateway=Gateway("Reusing it saves AED 9,999."))
        self.assertFalse(out["ok"])
        self.assertEqual(out["status"], "UNCHECKED_NUMBERS")

    def test_payload_has_no_names_of_people(self):
        g = Gateway("Fine.")
        advice.explain_with_ai(self.w.custodian, self.a, gateway=g)
        self.assertNotIn("Cara", str(g.payload))
        self.assertEqual(g.payload["rule_result"]["action"], EndOfLifeAction.RETAIN)
