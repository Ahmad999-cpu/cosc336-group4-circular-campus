from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.blueprint.models import ApprovalRule
from apps.catalogue.models import Asset
from apps.common.errors import Forbidden, InvalidTransition, SelfApproval, ValidationFailed
from apps.notifications.models import Notification
from apps.resource_requests.models import RequestStatus
from apps.transfers import services
from apps.transfers.models import DeliveryEventType, TransferStatus

from .factories import World, role, user


class WorkflowTests(TestCase):
    def setUp(self):
        self.w = World(qty=2)

    def test_reject_needs_reason_and_notifies(self):
        req = self.w.request()
        with self.assertRaises(ValidationFailed):
            services.reject_request(req.pk, self.w.approver, " ")
        services.reject_request(req.pk, self.w.approver, "Lab needs them this term")
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.REJECTED)
        self.assertTrue(Notification.objects.filter(recipient=self.w.requester, event_type="REQUEST_REJECTED").exists())
        with self.assertRaises(Exception):
            services.reject_request(req.pk, self.w.approver, "again")

    def test_cannot_reject_own_request(self):
        boss = user("Boss", self.w.me, (self.w.r_req, self.w.me), (self.w.r_app, self.w.eng))
        req = self.w.request(who=boss)
        with self.assertRaises(SelfApproval):
            services.reject_request(req.pk, boss, "no")

    def test_cancel_after_approval_releases_once(self):
        req = self.w.request(qty=2)
        services.approve_request(req.pk, self.w.approver)
        self.assertEqual(Asset.objects.get(pk=self.w.asset.pk).reserved_quantity, 2)
        services.cancel_reservation(req.pk, self.w.requester, "Plans changed")
        a = Asset.objects.get(pk=self.w.asset.pk)
        self.assertEqual((a.reserved_quantity, a.unreserved_quantity), (0, 2))
        with self.assertRaises(Exception):
            services.cancel_reservation(req.pk, self.w.requester, "again")
        self.assertEqual(Asset.objects.get(pk=self.w.asset.pk).reserved_quantity, 0)

    def test_no_cancel_after_dispatch(self):
        req = self.w.request()
        t = services.approve_request(req.pk, self.w.approver).transfer
        services.dispatch(t.pk, self.w.facilities, "van")
        with self.assertRaises(ValidationFailed):
            services.cancel_reservation(req.pk, self.w.requester, "too late")

    def test_only_facilities_dispatch(self):
        t = services.approve_request(self.w.request().pk, self.w.approver).transfer
        with self.assertRaises(Forbidden):
            services.dispatch(t.pk, self.w.requester, "van")

    def test_open_discrepancy_blocks_receipt_until_resolved(self):
        t = services.approve_request(self.w.request().pk, self.w.approver).transfer
        services.dispatch(t.pk, self.w.facilities, "van")
        ev = services.record_delivery_event(t.pk, self.w.requester, DeliveryEventType.DISCREPANCY, "Box damaged")
        with self.assertRaises(ValidationFailed):
            services.confirm_receipt(t.pk, self.w.requester, 1)
        services.resolve_event(ev.pk, self.w.facilities)
        services.confirm_receipt(t.pk, self.w.requester, 1, replaced_planned_purchase=True)
        t.refresh_from_db()
        self.assertEqual(t.status, TransferStatus.COMPLETED)
        self.assertTrue(t.replaced_planned_purchase)

    def test_blueprint_rule_routes_to_a_role(self):
        dean = role("Dean", "request.approve")
        ApprovalRule.objects.create(name="Monitors go to the dean", priority=1, category=self.w.category, approver_role=dean,
                                    approver_scope="INSTITUTION")
        req = self.w.request()
        problem = services.approval_problem(self.w.approver, req)
        self.assertIsInstance(problem, Forbidden)
        d = user("Dina", self.w.uni, (dean, None))
        services.approve_request(req.pk, d)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.APPROVED)

    def test_queue_and_counts(self):
        req = self.w.request()
        self.assertEqual(services.pending_count(self.w.approver), 1)
        services.approve_request(req.pk, self.w.approver)
        self.assertEqual(services.pending_count(self.w.approver), 0)
        self.assertEqual(services.to_dispatch_count(self.w.facilities), 1)


@override_settings(ALLOWED_HOSTS=["testserver"])
class ScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=1)
        self.w.asset.estimated_value = Decimal("650")
        self.w.asset.save(update_fields=["estimated_value"])
        self.h = {"HTTP_HX_REQUEST": "true"}

    def test_queue_explains_blocked_requests(self):
        r1, r2 = self.w.request(), self.w.request(who=self.w.requester2)
        self.client.force_login(self.w.approver)
        r = self.client.get(reverse("transfers:queue"))
        self.assertContains(r, "Competes with 1 other request")
        r = self.client.post(reverse("transfers:approve", args=[r1.pk]), {"v": r1.row_version}, **self.h)
        self.assertContains(r, "Only 0 unit(s) free now")
        self.assertIn("cc:toast", r["HX-Trigger-After-Settle"])

    def test_queue_is_for_approvers(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("transfers:queue")).status_code, 403)

    def test_stale_approval_is_a_conflict_toast(self):
        req = self.w.request()
        self.client.force_login(self.w.approver)
        r = self.client.post(reverse("transfers:approve", args=[req.pk]), {"v": req.row_version + 5}, **self.h)
        self.assertEqual(r.status_code, 204)
        self.assertIn("changed while you were looking", r["HX-Trigger-After-Settle"])

    def test_full_flow_through_the_screens(self):
        req = self.w.request()
        self.client.force_login(self.w.approver)
        self.client.post(reverse("transfers:approve", args=[req.pk]), {"v": req.row_version}, **self.h)
        t = services.transfer_for_request(req)
        self.client.force_login(self.w.facilities)
        r = self.client.post(reverse("transfers:dispatch", args=[t.pk]), {"how": "Facilities van", "note": "Tue 10:00"}, **self.h)
        self.assertContains(r, "On the way")
        self.client.force_login(self.w.requester)
        self.assertContains(self.client.get(reverse("transfers:receive", args=[req.pk]), **self.h), "How many arrived")
        r = self.client.post(reverse("transfers:receive", args=[req.pk]), {"quantity": "1", "replaced": "1"}, **self.h)
        self.assertEqual(r["HX-Redirect"], reverse("resource_requests:mine"))
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.FULFILLED)

    def test_short_delivery_records_discrepancy(self):
        w = World(qty=3)
        req = w.request(qty=2)
        t = services.approve_request(req.pk, w.approver).transfer
        services.dispatch(t.pk, w.facilities, "van")
        self.client.force_login(w.requester)
        self.client.post(reverse("transfers:receive", args=[req.pk]), {"quantity": "1"}, **self.h)
        t.refresh_from_db()
        self.assertEqual(t.status, TransferStatus.IN_TRANSIT)
        self.assertTrue(t.has_open_discrepancy())

    def test_receipt_before_dispatch_refused(self):
        req = self.w.request()
        t = services.approve_request(req.pk, self.w.approver).transfer
        with self.assertRaises(InvalidTransition):
            services.confirm_receipt(t.pk, self.w.requester, 1)
