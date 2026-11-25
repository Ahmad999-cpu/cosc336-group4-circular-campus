from decimal import Decimal

from django.test import SimpleTestCase

from apps.sustainability.calculator import estimate_savings, monthly_price


class CalculatorTests(SimpleTestCase):
    def test_worked_example(self):
        e = estimate_savings("asset_intensive", 1000, "typical")
        self.assertEqual((e.active_users, e.annual_savings, e.annual_subscription), (Decimal("120.00"), Decimal("58800"), Decimal("29400")))
        self.assertEqual((e.return_multiple, e.payback_months), (Decimal("2.00"), Decimal("6.0")))

    def test_conservative_participation(self):
        self.assertEqual(estimate_savings("asset_intensive", 1000, "conservative").return_multiple, Decimal("1.00"))

    def test_smallest_band_at_250_staff(self):
        got = [estimate_savings(t, 250).return_multiple for t in ("asset_intensive", "medium", "low")]
        self.assertEqual(got, [Decimal("1.17"), Decimal("1.32"), Decimal("1.18")])

    def test_price_bands(self):
        self.assertEqual([monthly_price("asset_intensive", s) for s in (499, 500, 4999, 5000, 10000)],
                         [1050, 2450, 2450, 3700, None])
