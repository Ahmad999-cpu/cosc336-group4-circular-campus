"""Phase 6: items that will be available in the future."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogue import services as cat
from apps.catalogue.models import Asset, AssetState
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed
from apps.lifecycle.models import LifeCycleEvent
from apps.matching import wishlist
from apps.matching.models import NeedStatus, SavedNeed
from apps.notifications.models import Notification, NotificationType
from apps.resource_requests import services as req

from .factories import World


class UpcomingTests(TestCase):
    def setUp(self):
        self.w = World()
        self.chairs = Asset.objects.create(name="Office chair", category=self.w.category, owner_department=self.w.cs,
                                           custodian=self.w.custodian, quantity=10, available_quantity=10, condition=Condition.GOOD,
                                           estimated_value=Decimal("380"), location_campus="Main")
        self.soon = timezone.localdate() + timedelta(days=40)

    def list_it(self, when=None):
        with self.captureOnCommitCallbacks(execute=True):
            return cat.set_expected_date(self.w.custodian, self.chairs, when or self.soon, "after the refit")

    def test_custodian_lists_an_item_as_coming_soon(self):
        a = self.list_it()
        self.assertTrue(a.is_upcoming)
        self.assertEqual(a.lifecycle_state, AssetState.REGISTERED)  # still not available: nothing else changes
        self.assertIn(a, cat.upcoming())
        self.assertNotIn(a, cat.published())
        self.assertTrue(LifeCycleEvent.objects.filter(asset=a, description__startswith="Expected available from").exists())

    def test_rules(self):
        with self.assertRaises(Forbidden):
            cat.set_expected_date(self.w.requester, self.chairs, self.soon)
        with self.assertRaises(ValidationFailed):
            cat.set_expected_date(self.w.custodian, self.chairs, timezone.localdate())
        with self.assertRaises(ValidationFailed):  # already available now
            cat.set_expected_date(self.w.custodian, self.w.asset, self.soon)
        Asset.objects.filter(pk=self.chairs.pk).update(lifecycle_state=AssetState.RETIRED)
        with self.assertRaises(ValidationFailed):
            cat.set_expected_date(self.w.custodian, self.chairs, self.soon)

    def test_cannot_be_requested_while_coming_soon(self):
        a = self.list_it()
        with self.assertRaises(ValidationFailed):
            req.submit_request(self.w.requester, {"department": self.w.me, "selected_asset": a, "quantity": 1, "purpose": "x",
                                                  "destination_campus": "Main"}, "k-soon")

    def test_anyone_signed_in_can_discover_it_but_there_is_no_request_button(self):
        self.list_it()
        self.client.force_login(self.w.requester)
        browse = self.client.get(reverse("catalogue:browse"))
        self.assertContains(browse, "Coming soon")
        self.assertContains(browse, "Office chair")
        panel = self.client.get(reverse("catalogue:panel", args=[self.chairs.pk]))
        self.assertContains(panel, "Coming soon: expected from")
        self.assertNotContains(panel, "Request this")
        self.assertContains(panel, "Tell me when it")

    def test_interest_is_not_a_reservation_and_is_told_when_ready(self):
        self.list_it()
        need = wishlist.express_interest(self.w.requester, self.chairs)
        self.assertTrue(need.is_interest)
        self.assertEqual(wishlist.express_interest(self.w.requester, self.chairs).pk, need.pk)  # once per person
        self.chairs.refresh_from_db()
        self.assertEqual(self.chairs.reserved_quantity, 0)
        with self.captureOnCommitCallbacks(execute=True):
            cat.confirm_condition(self.w.custodian, self.chairs, Condition.GOOD)
        with self.captureOnCommitCallbacks(execute=True):
            a = cat.publish(self.w.custodian, Asset.objects.get(pk=self.chairs.pk))
        self.assertIsNone(a.expected_available_on)  # really available now
        n = Notification.objects.filter(recipient=self.w.requester, event_type=NotificationType.NEED_MATCH, channel="IN_APP")
        self.assertEqual(n.count(), 1)
        self.assertIn("Office chair is now available", n.get().message)

    def test_changed_date_and_cancellation_are_told(self):
        self.list_it()
        wishlist.express_interest(self.w.requester, self.chairs)
        later = self.soon + timedelta(days=14)
        self.list_it(later)
        msgs = Notification.objects.filter(recipient=self.w.requester, event_type=NotificationType.AVAILABILITY, channel="IN_APP")
        self.assertEqual(msgs.count(), 1)
        self.assertIn("is now expected from", msgs.first().message)
        with self.captureOnCommitCallbacks(execute=True):
            cat.cancel_expected_date(self.w.custodian, Asset.objects.get(pk=self.chairs.pk), "stays in ME")
        self.assertEqual(msgs.count(), 2)
        self.assertEqual(SavedNeed.objects.get(owner=self.w.requester).status, NeedStatus.INACTIVE)
        self.assertNotIn(self.chairs, cat.upcoming())

    def test_overdue_date_is_shown_clearly(self):
        self.list_it()
        Asset.objects.filter(pk=self.chairs.pk).update(expected_available_on=timezone.localdate() - timedelta(days=3))
        a = Asset.objects.get(pk=self.chairs.pk)
        self.assertTrue(a.is_overdue)
        self.client.force_login(self.w.requester)
        self.assertContains(self.client.get(reverse("catalogue:panel", args=[a.pk])), "date passed")

    def test_interest_rules(self):
        with self.assertRaises(ValidationFailed):  # not listed
            wishlist.express_interest(self.w.requester, self.chairs)
        self.list_it()
        with self.assertRaises(Forbidden):
            wishlist.express_interest(self.w.custodian, self.chairs)

    def test_screens_for_the_custodian(self):
        self.client.force_login(self.w.custodian)
        r = self.client.post(reverse("catalogue:upcoming", args=[self.chairs.pk]), {"when": self.soon.isoformat(), "note": "refit"},
                             HTTP_HX_REQUEST="true")
        self.assertContains(r, "Change expected date")
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.post(reverse("catalogue:upcoming", args=[self.chairs.pk]), {"when": self.soon.isoformat()}).status_code, 403)
        r = self.client.post(reverse("matching:interest", args=[self.chairs.pk]), HTTP_HX_REQUEST="true")
        self.assertContains(r, "This is not a reservation")
        self.assertContains(self.client.get(reverse("matching:saved")), "Coming-soon items you asked about")
