"""Feature 3: check the catalogue before buying. Reuses matching and the net-cost formula; never requests."""
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from apps.catalogue.models import Asset, Category
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed
from apps.matching import procurement
from apps.matching.models import MatchResultSet
from apps.resource_requests.models import ResourceRequest

from .factories import World, role, user


class ProcurementTests(TestCase):
    def setUp(self):
        self.w = World(qty=2, value="650")  # CS owns 2 Dell monitors, AED 650 each, published
        self.w.asset.specifications = "24 inch, HDMI"
        self.w.asset.save(update_fields=["specifications"])
        self.chairs = Category.objects.create(name="Chairs")

    def plan(self, **kw):
        d = dict(description="24-inch monitors for the robotics lab", quantity=2, campus="Main")
        d.update(kw)
        return procurement.Plan(**d)

    def test_finds_the_item_and_uses_the_shared_saving_formula(self):
        res = procurement.check(self.w.requester, self.plan())
        self.assertTrue(res.ranked)
        a = res.alternatives[0]
        self.assertEqual(a.asset.pk, self.w.asset.pk)
        self.assertEqual(a.take, 2)
        self.assertEqual(a.buy_new, Decimal("1300"))
        self.assertEqual(a.reuse_cost, Decimal("40"))   # same campus transfer, Good condition: no repair
        self.assertEqual(a.avoided, Decimal("1260"))
        self.assertEqual((res.covered, res.still_to_buy, res.combined_avoided), (2, 0, Decimal("1260")))

    def test_fewer_units_than_needed_is_a_partial_match(self):
        res = procurement.check(self.w.requester, self.plan(quantity=5))
        a = res.alternatives[0]
        self.assertEqual(a.take, 2)
        self.assertIn("Only 2 of the 5 units you need are free.", a.partial)
        self.assertEqual((res.covered, res.still_to_buy), (2, 3))

    def test_specifications_are_reported_as_unverified(self):
        res = procurement.check(self.w.requester, self.plan(specifications="HDMI"))
        self.assertTrue(any("nobody has checked them" in p for p in res.alternatives[0].partial))
        res = procurement.check(self.w.requester, self.plan(specifications="DisplayPort USB-C"))
        if res.alternatives:
            self.assertTrue(any("Only some of your specifications" in p for p in res.alternatives[0].partial))

    def test_your_price_replaces_the_item_value(self):
        res = procurement.check(self.w.requester, self.plan(unit_price=Decimal("900")))
        a = res.alternatives[0]
        self.assertEqual(a.buy_new, Decimal("1800"))
        self.assertEqual(a.price_source, "your estimated price")

    def test_savings_are_counted_once_across_alternatives(self):
        Asset.objects.create(name="HP 24-inch monitor", category=self.w.category, owner_department=self.w.cs, custodian=self.w.custodian,
                             quantity=3, available_quantity=3, condition=Condition.GOOD, estimated_value=Decimal("600"),
                             specifications="24 inch", location_campus="Main")
        hp = Asset.objects.get(name="HP 24-inch monitor")
        hp.mark_available(self.w.custodian); hp.publish(self.w.custodian)
        res = procurement.check(self.w.requester, self.plan(quantity=2))
        self.assertGreaterEqual(len(res.alternatives), 2)
        self.assertEqual(res.covered, 2)
        best = res.alternatives[0]
        self.assertEqual(res.combined_avoided, best.avoided)  # the best item covers both units; nothing added twice
        self.assertLess(res.combined_avoided, sum(a.avoided for a in res.alternatives))

    def test_nothing_suitable(self):
        res = procurement.check(self.w.requester, self.plan(description="bunsen burner for chemistry", category=self.chairs))
        self.assertEqual(res.alternatives, [])
        self.assertEqual(res.covered, 0)

    def test_own_unit_items_and_unpublished_items_are_not_offered(self):
        cs_requester = user("Cy", self.w.cs, (self.w.r_req, self.w.cs))
        self.assertEqual(procurement.check(cs_requester, self.plan()).alternatives, [])
        from apps.catalogue import services as cat
        cat.unpublish(self.w.custodian, self.w.asset)
        self.assertEqual(procurement.check(self.w.requester, self.plan()).alternatives, [])

    def test_never_requests_or_reserves(self):
        before = (ResourceRequest.objects.count(), self.w.asset.reserved_quantity)
        procurement.check(self.w.requester, self.plan())
        self.w.asset.refresh_from_db()
        self.assertEqual(before, (ResourceRequest.objects.count(), self.w.asset.reserved_quantity))
        self.assertEqual(MatchResultSet.objects.count(), 1)  # logged like every Find search

    def test_permissions_and_validation(self):
        with self.assertRaises(Forbidden):
            procurement.check(self.w.custodian, self.plan())
        self.assertTrue(procurement.may_check(self.w.approver))
        with self.assertRaises(ValidationFailed):
            procurement.check(self.w.requester, self.plan(description=" "))
        with self.assertRaises(ValidationFailed):
            procurement.check(self.w.requester, self.plan(unit_price=Decimal("-1")))

    def test_matching_unavailable_falls_back_to_keywords(self):
        with mock.patch("apps.matching.services.embed_model", side_effect=RuntimeError("index down")):
            res = procurement.check(self.w.requester, self.plan(description="Dell monitor"))
        self.assertFalse(res.ranked)
        self.assertEqual(res.combined_from, [])
        self.assertIn("Not ranked: keyword match only, so check that it fits.", res.alternatives[0].partial)


class ProcurementScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=2)

    def test_page_and_results(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("matching:procure"))
        self.assertContains(r, "Check before buying")
        r = self.client.get(reverse("matching:procure"), {"description": "monitor for the lab", "quantity": 4, "campus": "Main"})
        self.assertContains(r, "Reuse could cover 2 of the 4 units")
        self.assertContains(r, "Only 2 of the 4 units you need are free.")
        self.assertContains(r, "Request 2 units")
        self.assertContains(r, "must not be added together")

    def test_approver_can_check_but_gets_no_request_button(self):
        self.client.force_login(self.w.approver)
        r = self.client.get(reverse("matching:procure"), {"description": "monitor", "quantity": 1})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Request 1 unit")

    def test_custodian_without_either_permission_is_refused(self):
        self.client.force_login(self.w.custodian)
        self.assertEqual(self.client.get(reverse("matching:procure")).status_code, 403)

    def test_signed_out_goes_to_sign_in(self):
        r = self.client.get(reverse("matching:procure"))
        self.assertEqual(r.status_code, 302)

    def test_invalid_input_is_explained(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("matching:procure"), {"description": "monitor", "quantity": 0})
        self.assertContains(r, "Ensure this value is greater than or equal to 1")
