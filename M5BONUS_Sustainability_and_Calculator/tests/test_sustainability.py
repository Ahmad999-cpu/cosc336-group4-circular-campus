"""C7 dashboard, impact recording on receipt, net-cost comparison, and the public calculator page."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.catalogue.models import Category
from apps.common.enums import Condition
from apps.resource_requests import services as req_services
from apps.sustainability import services
from apps.sustainability.models import EmissionFactor, ImpactType, SustainabilityImpact
from apps.transfers import services as tr

from .factories import World


class Flow(TestCase):
    def setUp(self):
        self.w = World(qty=5)  # Dell monitor, AED 650, CS on Main

    def receive(self, qty=2, verified=False, campus="Main"):
        r, _ = req_services.submit_request(self.w.requester, {
            "department": self.w.me, "selected_asset": self.w.asset, "quantity": qty, "purpose": "Lab",
            "destination_campus": campus}, uuid.uuid4().hex)
        tr.approve_request(r.pk, self.w.approver)
        t = tr.transfer_for_request(r)
        tr.dispatch(t.pk, self.w.facilities, "Van")
        tr.confirm_receipt(t.pk, self.w.requester, qty, replaced_planned_purchase=verified)
        return t


class ImpactTests(Flow):
    def test_receipt_records_avoided_purchase_net_of_transfer(self):
        t = self.receive(2)
        imp = SustainabilityImpact.objects.get(transfer=t)  # no factor yet: only the money figure
        self.assertEqual(imp.impact_type, ImpactType.AVOIDED_PURCHASE)
        self.assertEqual(imp.avoided_cost, Decimal("1260"))  # 2 × 650 − 40 same campus
        self.assertTrue(imp.is_estimate)

    def test_verified_carbon_and_waste_with_a_parent_factor(self):
        it = Category.objects.create(name="IT")
        self.w.category.parent = it
        self.w.category.save()
        EmissionFactor.objects.create(category=it, kg_co2e_per_unit=Decimal("300"), mass_kg_per_unit=Decimal("5"),
                                      source="Local study", source_date=date(2026, 1, 1))
        t = self.receive(2, verified=True, campus="SAN")
        kinds = {i.impact_type: i for i in SustainabilityImpact.objects.filter(transfer=t)}
        self.assertEqual(kinds[ImpactType.VERIFIED_AVOIDED_PURCHASE].avoided_cost, Decimal("1180"))  # − 120 other campus
        self.assertFalse(kinds[ImpactType.VERIFIED_AVOIDED_PURCHASE].is_estimate)
        self.assertEqual(kinds[ImpactType.CARBON_REDUCTION].co2e_kg, Decimal("600"))
        self.assertEqual(kinds[ImpactType.WASTE_DIVERSION].mass_kg, Decimal("10"))
        self.assertEqual(len(services.record_transfer_impact(t)), 3)  # idempotent
        self.assertEqual(SustainabilityImpact.objects.filter(transfer=t).count(), 3)


class DashboardTests(Flow):
    def test_measures_with_formula_and_source_and_unavailable_not_zero(self):
        self.receive(2)
        d = services.dashboard_measures()
        m = {x.key: x for x in d.measures}
        self.assertEqual(m["units"].value, 2)
        self.assertEqual(m["avoided"].value, Decimal("1260"))
        self.assertIsNone(m["co2e"].value)  # no factor -> unavailable, never 0
        self.assertIsNone(m["waste"].value)
        self.assertEqual(m["rate"].value, 100)
        for x in d.measures:
            self.assertTrue(x.formula and x.source)
        self.assertEqual(d.by_category[0]["units"], 2)
        self.assertEqual(sum(b["units"] for b in d.by_month), 2)

    def test_period_filter(self):
        self.receive(1)
        old = services.dashboard_measures(None, date.today() - timedelta(days=400), date.today() - timedelta(days=300))
        self.assertEqual(old.measures[0].value, 0)

    def test_page(self):
        self.receive(1)
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("sustainability:dashboard"), {"period": "all"})
        self.assertContains(r, "How it")
        self.assertContains(r, "Unavailable")
        self.assertContains(r, "Locally selected carbon factors")
        self.assertNotContains(r, "official")


class NetCostTests(Flow):
    def test_defaults_and_overrides(self):
        nc = services.net_cost_comparison(self.w.asset, 2, destination_campus="Main")
        self.assertEqual((nc.buy_new, nc.transport, nc.repair, nc.avoided, nc.feasible), (Decimal("1300"), Decimal("40"), Decimal("0"), Decimal("1260"), "yes"))
        nc = services.net_cost_comparison(self.w.asset, 2, new_unit_price="10", transport="100", destination_campus="Main")
        self.assertEqual(nc.avoided, Decimal("-80"))
        self.assertFalse(nc.reuse_wins)
        self.assertIn("Buying new is cheaper with these inputs.", nc.reasons)

    def test_feasibility(self):
        self.assertEqual(services.net_cost_comparison(self.w.asset, 9).feasible, "no")
        self.w.asset.condition = Condition.POOR
        nc = services.net_cost_comparison(self.w.asset, 1, destination_campus="Main")
        self.assertEqual(nc.feasible, "repair")
        self.assertEqual(nc.repair, Decimal("130.00"))  # 20 % of 650
        tight = services.net_cost_comparison(self.w.asset, 1, destination_campus="Main", required_date=date.today() + timedelta(days=1))
        self.assertTrue(any("ready" in r for r in tight.reasons))

    def test_drawer_and_live_update(self):
        self.client.force_login(self.w.requester)
        url = reverse("sustainability:compare", args=[self.w.asset.pk])
        self.assertContains(self.client.get(url), "Reuse or buy new?")
        r = self.client.get(url, {"qty": 3, "price": "700"}, HTTP_HX_REQUEST="true", HTTP_HX_TARGET="nc-out")
        self.assertContains(r, "AED 2,100")
        self.assertNotContains(r, "drawer-head")


class CalculatorPageTests(TestCase):
    def test_public_worked_example(self):
        r = self.client.get(reverse("sustainability:calculator"))  # no sign-in needed
        self.assertEqual(r.status_code, 200)
        for text in ("AED 58,800", "AED 2,450", "2×", "6 months", "Universities, hospitals, labs", "AED 490"):
            self.assertContains(r, text)

    def test_quote_and_bad_input(self):
        r = self.client.get(reverse("sustainability:calculator"), {"staff": "12000", "type": "low", "part": "high"},
                            HTTP_HX_REQUEST="true", HTTP_HX_TARGET="calc-out")
        self.assertContains(r, "Custom quote")
        self.assertEqual(self.client.get(reverse("sustainability:calculator"), {"staff": "lots", "type": "x"}).status_code, 200)
