import threading

from django.db import connection
from django.test import TestCase, TransactionTestCase

from apps.catalogue.models import Asset, AssetState
from apps.common.errors import Forbidden, InsufficientQuantity, InvalidTransition, SelfApproval
from apps.resource_requests.models import RequestStatus
from apps.transfers.models import TransferStatus
from apps.transfers.services import approve_request, confirm_receipt

from .factories import World, user


class ApprovalTests(TestCase):
    def setUp(self):
        self.w = World(qty=1)

    def test_no_self_approval(self):
        boss = user("Boss", self.w.me, (self.w.r_req, self.w.me), (self.w.r_app, self.w.eng))
        req = self.w.request(who=boss)
        with self.assertRaises(SelfApproval):
            approve_request(req.pk, boss)

    def test_user_without_approve_permission_is_refused(self):
        req = self.w.request()
        with self.assertRaises(Forbidden):
            approve_request(req.pk, self.w.requester2)

    def test_approval_limit_from_role(self):
        self.w.asset.estimated_value = 5000  # above the Approver role's AED 2,000 limit
        self.w.asset.save(update_fields=["estimated_value"])
        with self.assertRaises(Forbidden):
            approve_request(self.w.request().pk, self.w.approver)

    def test_last_unit_cannot_go_to_two_people(self):
        r1, r2 = self.w.request(), self.w.request(who=self.w.requester2)
        approve_request(r1.pk, self.w.approver)
        with self.assertRaises(InsufficientQuantity):
            approve_request(r2.pk, self.w.approver)
        r2.refresh_from_db()
        self.assertEqual(r2.status, RequestStatus.PENDING_APPROVAL)

    def test_receiver_confirms_and_custody_moves(self):
        req = self.w.request()
        reservation = approve_request(req.pk, self.w.approver)
        transfer = reservation.transfer
        a = Asset.objects.get(pk=self.w.asset.pk)
        self.assertEqual(a.owner_department, self.w.cs)  # approval never moves custody
        transfer.dispatch("trolley, Tuesday", self.w.facilities)
        moved = confirm_receipt(transfer.pk, self.w.requester, 1)
        self.assertEqual((moved.owner_department, moved.custodian, moved.lifecycle_state),
                         (self.w.me, self.w.requester, AssetState.TRANSFERRED))
        transfer.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual((transfer.status, req.status), (TransferStatus.COMPLETED, RequestStatus.FULFILLED))

    def test_partial_lot_is_split(self):
        w = World(qty=5)
        w.r_app.approval_limit = None
        w.r_app.save()
        req = w.request(qty=2)
        t = approve_request(req.pk, w.approver).transfer
        t.dispatch("", w.facilities)
        moved = confirm_receipt(t.pk, w.requester, 2)
        original = Asset.objects.get(pk=w.asset.pk)
        self.assertNotEqual(moved.pk, original.pk)
        self.assertEqual((original.quantity, original.reserved_quantity, moved.quantity), (3, 0, 2))

    def test_receipt_before_dispatch_is_refused(self):
        t = approve_request(self.w.request().pk, self.w.approver).transfer
        with self.assertRaises(InvalidTransition):
            confirm_receipt(t.pk, self.w.requester, 1)


class ConcurrentApprovalTests(TransactionTestCase):
    """Two approvers click 'approve' at the same moment for the last unit: exactly one wins."""

    def test_parallel_approvals(self):
        w = World(qty=1)
        second_approver = user("Ali", w.eng, (w.r_app, w.eng))
        r1, r2 = w.request(), w.request(who=w.requester2)
        barrier, results = threading.Barrier(2), []

        def run(req, who):
            try:
                barrier.wait()
                approve_request(req.pk, who)
                results.append("ok")
            except InsufficientQuantity:
                results.append("refused")
            finally:
                connection.close()

        threads = [threading.Thread(target=run, args=(r1, w.approver)), threading.Thread(target=run, args=(r2, second_approver))]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(results), ["ok", "refused"])
        a = Asset.objects.get(pk=w.asset.pk)
        self.assertEqual(a.reserved_quantity, 1)
