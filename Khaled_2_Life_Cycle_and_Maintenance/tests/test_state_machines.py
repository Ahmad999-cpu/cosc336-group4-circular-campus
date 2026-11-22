from django.test import TestCase

from apps.catalogue.models import AssetState
from apps.common.errors import InsufficientQuantity, InvalidTransition, ValidationFailed
from apps.lifecycle.models import LifeCycleEvent

from .factories import World


class AssetStateMachineTests(TestCase):
    def setUp(self):
        self.w = World(qty=2)
        self.a = self.w.asset

    def test_every_operation_writes_history(self):
        kinds = list(LifeCycleEvent.objects.filter(asset=self.a).values_list("event_type", flat=True))
        self.assertEqual(kinds, ["STATE_CHANGE", "PUBLICATION"])

    def test_disallowed_transition_is_refused(self):
        with self.assertRaises(InvalidTransition):
            self.a.change_state(AssetState.DONATED, self.w.custodian, approval_ref=object())

    def test_end_of_life_needs_approval_reference(self):
        with self.assertRaises(ValidationFailed):
            self.a.change_state(AssetState.RETIRED, self.w.custodian)

    def test_cannot_reserve_more_than_free(self):
        self.a.allocate(2, self.w.approver)
        self.assertEqual(self.a.lifecycle_state, AssetState.RESERVED)
        with self.assertRaises(InsufficientQuantity):
            self.a.allocate(1, self.w.approver)

    def test_release_returns_units_once(self):
        self.a.allocate(2, self.w.approver)
        self.a.release(2, self.w.approver)
        self.assertEqual((self.a.reserved_quantity, self.a.lifecycle_state), (0, AssetState.AVAILABLE))
        with self.assertRaises(ValidationFailed):
            self.a.release(1, self.w.approver)

    def test_no_maintenance_while_reserved(self):
        self.a.allocate(1, self.w.approver)
        with self.assertRaises(ValidationFailed):
            self.a.change_state(AssetState.UNDER_MAINTENANCE, self.w.custodian)

    def test_generic_edit_cannot_touch_state(self):
        with self.assertRaises(ValidationFailed):
            self.a.update({"lifecycle_state": AssetState.DISPOSED}, self.w.custodian)

    def test_history_is_append_only(self):
        ev = LifeCycleEvent.objects.filter(asset=self.a).first()
        ev.description = "changed"
        with self.assertRaises(ValidationFailed):
            ev.save()
        with self.assertRaises(ValidationFailed):
            ev.delete()
