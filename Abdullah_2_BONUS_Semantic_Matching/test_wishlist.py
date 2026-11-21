"""Phase 5: saved needs and availability alerts."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogue import services as cat
from apps.catalogue.models import Asset, Category
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed
from apps.matching import wishlist
from apps.matching.models import NeedMatch, NeedStatus, SavedNeed
from apps.notifications.models import Notification, NotificationType
from apps.resource_requests.models import ResourceRequest

from .factories import World, user


class WishlistTests(TestCase):
    def setUp(self):
        self.w = World(qty=1)
        cat.unpublish(self.w.custodian, self.w.asset)  # nothing published at first
        self.data = {"description": "Two 24-inch monitors for the robotics lab", "quantity": 2, "specifications": "24 inch",
                     "category": None, "preferred_condition": "ANY", "campus": "Main", "needed_by": None}

    def alerts(self, who=None):
        return Notification.objects.filter(recipient=who or self.w.requester, event_type=NotificationType.NEED_MATCH, channel="IN_APP")

    def publish(self, asset):
        with self.captureOnCommitCallbacks(execute=True):
            cat.publish(self.w.custodian, asset)

    def new_monitor(self, qty=2, **kw):
        a = Asset.objects.create(name=kw.pop("name", "Samsung 24-inch monitor"), category=self.w.category, owner_department=self.w.cs,
                                 custodian=self.w.custodian, quantity=qty, available_quantity=qty, condition=Condition.GOOD,
                                 estimated_value=Decimal("700"), specifications="24 inch, HDMI", location_campus="Main", **kw)
        a.mark_available(self.w.custodian)
        return a

    def test_save_with_nothing_published_then_alert_on_publication(self):
        need, found = wishlist.save_need(self.w.requester, self.data)
        self.assertEqual(found, [])
        self.publish(self.new_monitor())
        self.assertEqual(self.alerts().count(), 1)
        n = self.alerts().get()
        self.assertIn("Samsung 24-inch monitor may fit your saved need", n.message)
        self.assertTrue(n.message_ar)  # stored in both languages
        self.assertTrue(n.subject_ref.startswith("Asset:"))  # links to the item
        self.assertEqual(ResourceRequest.objects.count(), 0)  # never requested
        a = Asset.objects.get(name="Samsung 24-inch monitor")
        self.assertEqual(a.reserved_quantity, 0)  # never reserved

    def test_same_unchanged_match_is_not_notified_twice(self):
        wishlist.save_need(self.w.requester, self.data)
        a = self.new_monitor()
        self.publish(a)
        with self.captureOnCommitCallbacks(execute=True):
            cat.unpublish(self.w.custodian, a)
        self.publish(a)
        wishlist.check_asset(a)
        self.assertEqual(self.alerts().count(), 1)

    def test_a_changed_match_is_notified_again(self):
        wishlist.save_need(self.w.requester, self.data)
        a = self.new_monitor(qty=1)
        self.publish(a)
        first = self.alerts().get()
        self.assertIn("only 1 of 2 units are free", first.message)  # partial match explained
        with self.captureOnCommitCallbacks(execute=True):
            cat.change_quantity(self.w.custodian, Asset.objects.get(pk=a.pk), 2)
        wishlist.check_asset(a)
        self.assertEqual(self.alerts().count(), 2)

    def test_items_already_there_are_shown_not_notified(self):
        self.publish(self.new_monitor())
        need, found = wishlist.save_need(self.w.requester, self.data)
        self.assertEqual(len(found), 1)
        self.assertEqual(self.alerts().count(), 0)
        wishlist.check_asset(found[0].asset)
        self.assertEqual(self.alerts().count(), 0)

    def test_unrelated_items_and_own_unit_items_do_not_match(self):
        wishlist.save_need(self.w.requester, self.data)
        chairs = Category.objects.create(name="Chairs")
        c = Asset.objects.create(name="Office chair", category=chairs, owner_department=self.w.cs, custodian=self.w.custodian,
                                 quantity=5, available_quantity=5, condition=Condition.GOOD, location_campus="Main")
        c.mark_available(self.w.custodian)
        self.publish(c)
        self.assertEqual(self.alerts().count(), 0)
        own = user("Cy", self.w.cs, (self.w.r_req, self.w.cs))
        wishlist.save_need(own, self.data)
        self.publish(self.new_monitor())
        self.assertEqual(self.alerts(own).count(), 0)

    def test_inactive_needs_are_not_checked(self):
        need, _f = wishlist.save_need(self.w.requester, self.data)
        wishlist.set_active(self.w.requester, need, False)
        self.publish(self.new_monitor())
        self.assertEqual(self.alerts().count(), 0)

    def test_only_the_owner_can_change_or_see_a_need(self):
        need, _f = wishlist.save_need(self.w.requester, self.data)
        for fn in (lambda: wishlist.set_active(self.w.requester2, need, False), lambda: wishlist.delete_need(self.w.requester2, need),
                   lambda: wishlist.update_need(self.w.requester2, need, self.data)):
            with self.assertRaises(Forbidden):
                fn()
        self.client.force_login(self.w.requester2)
        self.assertNotContains(self.client.get(reverse("matching:saved")), "Two 24-inch monitors for the robotics lab")
        self.assertEqual(self.client.post(reverse("matching:need_action", args=[need.pk, "delete"])).status_code, 404)
        self.assertTrue(SavedNeed.objects.filter(pk=need.pk).exists())

    def test_validation(self):
        for bad in ({"description": "x"}, {"quantity": 0}, {"needed_by": timezone.localdate() - timedelta(days=1)}):
            with self.assertRaises(ValidationFailed):
                wishlist.save_need(self.w.requester, {**self.data, **bad})
        with self.assertRaises(Forbidden):
            wishlist.save_need(self.w.custodian, self.data)

    def test_edit_rechecks_and_delete_removes(self):
        self.publish(self.new_monitor())
        need, found = wishlist.save_need(self.w.requester, {**self.data, "description": "bunsen burner", "specifications": ""})
        self.assertEqual(found, [])
        need, found = wishlist.update_need(self.w.requester, need, self.data)
        self.assertEqual(len(found), 1)
        wishlist.delete_need(self.w.requester, need)
        self.assertFalse(NeedMatch.objects.exists())

    def test_matching_unavailable_keeps_the_need_and_publishing_still_works(self):
        need, _f = wishlist.save_need(self.w.requester, self.data)
        with mock.patch("apps.matching.wishlist.get_embedder", side_effect=RuntimeError("model down")):
            a = self.new_monitor()
            self.publish(a)  # must not raise
        a.refresh_from_db()
        self.assertEqual(a.publication_status, "PUBLISHED")
        need.refresh_from_db()
        self.assertTrue(need.check_failed)
        self.assertEqual(self.alerts().count(), 0)


class WishlistScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=1)
        self.client.force_login(self.w.requester)

    def test_save_from_the_list_and_see_matches(self):
        r = self.client.post(reverse("matching:need_new"), {"description": "Dell monitor for the lab", "quantity": 3, "from": "list"},
                             HTTP_HX_REQUEST="true")
        self.assertContains(r, "Dell monitor")
        self.assertContains(r, "Covers 1 of 3")  # partial, from the published World monitor
        page = self.client.get(reverse("matching:saved"))
        self.assertContains(page, "Deactivate")
        self.assertContains(page, "Saved needs")

    def test_actions(self):
        need, _f = wishlist.save_need(self.w.requester, {"description": "Dell monitor", "quantity": 1})
        for action, status in (("deactivate", NeedStatus.INACTIVE), ("activate", NeedStatus.ACTIVE)):
            self.client.post(reverse("matching:need_action", args=[need.pk, action]), HTTP_HX_REQUEST="true")
            need.refresh_from_db()
            self.assertEqual(need.status, status)
        r = self.client.post(reverse("matching:need_action", args=[need.pk, "check"]), HTTP_HX_REQUEST="true")
        self.assertContains(r, "Dell monitor")
        self.client.post(reverse("matching:need_action", args=[need.pk, "delete"]), HTTP_HX_REQUEST="true")
        self.assertFalse(SavedNeed.objects.filter(pk=need.pk).exists())

    def test_requesters_only(self):
        self.client.force_login(self.w.custodian)
        self.assertEqual(self.client.get(reverse("matching:saved")).status_code, 403)
