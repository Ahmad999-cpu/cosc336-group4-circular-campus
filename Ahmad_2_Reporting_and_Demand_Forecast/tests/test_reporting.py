"""Reporting: C9 rows, totals and CSV; AI feature 5 draft → edit → publish; the AI never sees names or changes numbers."""
import csv
import io
import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.ai.gateway import AIGateway
from apps.ai.models import AICapability, AIOutcome, ModelVersion
from apps.ai.result import AIResult
from apps.common.errors import Forbidden, ValidationFailed
from apps.reporting import services
from apps.reporting.models import AISummary, Report, ReportType, SummaryStatus
from apps.resource_requests import services as req_services
from apps.transfers import services as tr

from .factories import World, role, user


class Base(TestCase):
    def setUp(self):
        self.w = World(qty=5)
        self.viewer = user("Vera", self.w.uni, (role("Reader", "reports.view"), self.w.eng))
        self.editor = user("Sara", self.w.uni, (role("Sustain", "reports.view", "reports.publish"), None))
        ModelVersion.objects.create(capability=AICapability.SUMMARIZE, provider="fake", model_name="fake", version="s1").activate()
        self.r1, _ = req_services.submit_request(self.w.requester, {
            "department": self.w.me, "selected_asset": self.w.asset, "quantity": 2, "purpose": "Lab",
            "destination_campus": "Main"}, uuid.uuid4().hex)
        self.r2, _ = req_services.submit_request(self.w.requester2, {
            "department": self.w.me, "selected_asset": self.w.asset, "quantity": 1, "purpose": "Desk",
            "destination_campus": "Main"}, uuid.uuid4().hex)
        tr.approve_request(self.r1.pk, self.w.approver)
        tr.reject_request(self.r2.pk, self.w.approver, "Not this term")
        t = tr.transfer_for_request(self.r1)
        tr.dispatch(t.pk, self.w.facilities, "Van, Monday")
        tr.confirm_receipt(t.pk, self.w.requester, 2, replaced_planned_purchase=True)
        self.f = services.Filters.default()


class TotalsAndRowsTests(Base):
    def test_totals_come_from_the_records(self):
        t = services.requests_transfers_totals(self.editor, self.f)
        self.assertEqual((t["requests"], t["units_requested"], t["approved"], t["rejected"], t["pending"]), (2, 3, 1, 1, 0))
        self.assertEqual(t["approval_rate_pct"], 50)
        self.assertEqual((t["transfers_completed"], t["units_moved"], t["value_reused_aed"], t["replaced_planned_purchases"]), (1, 2, 1300, 1))
        self.assertEqual(t["top_categories"], [{"category": "Monitors", "requests": 2}])

    def test_rows_and_csv_match(self):
        cols, rows, _ = services.build(self.editor, self.f)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["transfer_status"] or rows[1]["transfer_status"], "Completed")
        name, body = services.export_csv(self.editor, self.f)
        parsed = list(csv.DictReader(io.StringIO(body.lstrip("﻿"))))
        self.assertEqual(len(parsed), 2)
        self.assertEqual(list(parsed[0].keys()), cols)
        self.assertTrue(Report.objects.filter(exported_at__isnull=False).exists())

    def test_period_and_scope(self):
        old = services.Filters(ReportType.REQUESTS_TRANSFERS, timezone.localdate() - timedelta(days=90), timezone.localdate() - timedelta(days=60))
        self.assertEqual(services.requests_transfers_totals(self.editor, old)["requests"], 0)
        outsider = user("Out", self.w.uni)
        with self.assertRaises(Forbidden):
            services.build(outsider, self.f)
        f = services.Filters.default()
        f.unit_id = str(self.w.uni.pk)  # above the viewer's Engineering scope
        with self.assertRaises(Forbidden):
            services.build(self.viewer, f)

    def test_available_items(self):
        f = services.Filters.default(ReportType.AVAILABLE_ASSETS)
        cols, rows, totals = services.build(self.editor, f)
        self.assertEqual((totals["items"], totals["free_units"]), (1, 3))
        self.assertEqual(rows[0]["free_units"], 3)


class SummaryTests(Base):
    def test_draft_edit_publish(self):
        out = services.generate_summary(self.editor, self.f)
        s = out.summary
        self.assertEqual(s.status, SummaryStatus.DRAFT)
        self.assertIn("2 requests", s.draft_text)
        self.assertEqual(out.unchecked, [])
        services.publish_summary(self.editor, s.pk, s.draft_text + " Checked.")
        s.refresh_from_db()
        self.assertEqual(s.status, SummaryStatus.ACCEPTED)
        self.assertNotEqual(s.final_text, s.draft_text)
        self.assertGreater(services.edit_distance_share(s), 0)
        with self.assertRaises(ValidationFailed):
            services.publish_summary(self.editor, s.pk, "Again, a second time.")
        published, draft = services.summaries_for(self.viewer, self.f)
        self.assertEqual([p.pk for p in published], [s.pk])
        self.assertIsNone(draft)

    def test_numbers_not_in_the_report_are_flagged(self):
        self.assertEqual(services.unchecked_numbers("2 requests, 50% approved, AED 1,300 reused.", services.requests_transfers_totals(self.editor, self.f), self.f), [])
        self.assertEqual(services.unchecked_numbers("We saved AED 9,999 and 2 requests.", services.requests_transfers_totals(self.editor, self.f), self.f), ["9,999"])

    def test_ai_input_has_no_names_and_at_most_200_rows(self):
        payload = services.summary_input(self.editor, self.f)
        self.assertNotIn("approved_by", payload["rows"][0])
        self.assertNotIn("Adam", str(payload))
        self.assertLessEqual(len(payload["rows"]), services.MAX_AI_ROWS)
        self.assertTrue(payload["limitations"])

    def test_report_still_works_when_ai_is_down(self):
        gw = mock.Mock(spec=AIGateway)
        gw.summarize.return_value = AIResult(AIOutcome.TIMEOUT)
        out = services.generate_summary(self.editor, self.f, gateway=gw)
        self.assertIsNone(out.summary)
        self.assertIn("too long", out.message)
        self.assertFalse(AISummary.objects.exists())

    def test_only_editors_write_and_publish(self):
        with self.assertRaises(Forbidden):
            services.generate_summary(self.viewer, self.f)
        s = services.generate_summary(self.editor, self.f).summary
        with self.assertRaises(Forbidden):
            services.publish_summary(self.viewer, s.pk, "A perfectly fine summary text.")
        with self.assertRaises(ValidationFailed):
            services.publish_summary(self.editor, s.pk, "short")
        services.discard_summary(self.editor, s.pk)
        s.refresh_from_db()
        self.assertEqual(s.status, SummaryStatus.REJECTED)


@override_settings(AI_PROVIDER="anthropic", ANTHROPIC_API_KEY="test-key", ANTHROPIC_MODEL="claude-haiku-5-5")
class AnthropicAdapterTests(TestCase):
    """The real adapter with the network call replaced: prompt shape and defensive parsing."""

    def setUp(self):
        from apps.ai.providers.anthropic import Provider
        self.p = Provider()
        self.mv = SimpleNamespace(provider="fake", model_name="fake")

    def reply(self, text):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])

    def test_summarize_parses_json_and_uses_the_configured_model(self):
        with mock.patch.object(self.p.client.messages, "create", return_value=self.reply(
                'Here you go: {"text": "2 requests in the period.", "claims": [{"value": "2", "source": "requests"}]}')) as create:
            r = self.p.summarize({"totals": {"requests": 2}, "language": "en"}, self.mv)
        self.assertEqual(r.status, AIOutcome.OK)
        self.assertEqual(r.value["text"], "2 requests in the period.")
        kw = create.call_args.kwargs
        self.assertEqual(kw["model"], "claude-haiku-5-5")
        self.assertIn("Use only numbers", kw["system"])
        self.assertIn('"requests": 2', kw["messages"][0]["content"])

    def test_bad_replies_are_errors_not_exceptions(self):
        for bad in ["no json at all", '{"text": ""}', '{"text": 5}']:
            with mock.patch.object(self.p.client.messages, "create", return_value=self.reply(bad)):
                self.assertEqual(self.p.summarize({}, self.mv).status, AIOutcome.ERROR)


class ScreenTests(Base):
    def test_page_csv_and_review_flow(self):
        self.client.force_login(self.editor)
        r = self.client.get(reverse("reporting:index"))
        self.assertContains(r, "Approval rate")
        self.assertContains(r, "Write a draft with AI")
        r = self.client.get(reverse("reporting:index"), {"type": "AVAILABLE_ASSETS"}, HTTP_HX_REQUEST="true", HTTP_HX_TARGET="report-body")
        self.assertContains(r, "Free units")
        self.assertNotContains(r, "<html")
        r = self.client.get(reverse("reporting:csv"))
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", r["Content-Disposition"])
        r = self.client.post(reverse("reporting:summarize"), {"type": "REQUESTS_TRANSFERS"}, HTTP_HX_REQUEST="true")
        self.assertContains(r, "AI draft")
        s = AISummary.objects.get()
        r = self.client.post(reverse("reporting:publish", args=[s.pk]), {"text": s.draft_text}, HTTP_HX_REQUEST="true")
        self.assertContains(r, "AI draft published as written")

    def test_viewer_sees_no_ai_button_and_others_get_403(self):
        self.client.force_login(self.viewer)
        self.assertNotContains(self.client.get(reverse("reporting:index")), "Write a draft with AI")
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("reporting:index")).status_code, 403)
