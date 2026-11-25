"""Feature 4: demand forecast from real request records; honest about too little data; sample never stored."""
from datetime import date, datetime, time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogue.models import Category
from apps.reporting import forecast
from apps.resource_requests.models import RequestStatus, ResourceRequest

from .factories import World, role, user

TODAY = date(2026, 11, 15)
_n = [0]


def at(d: date):
    return timezone.make_aware(datetime.combine(d, time(10)))


class DemandTests(TestCase):
    def setUp(self):
        self.w = World()
        self.chairs = Category.objects.create(name="Chairs")
        self.officer = user("Sara", self.w.uni, (role("Officer", "reports.view"), None))

    def req(self, d: date, qty=1, category=None, dept=None, status=None):
        _n[0] += 1
        r = ResourceRequest.objects.create(requester=self.w.requester, department=dept or self.w.me, category=category or self.w.category,
                                           purpose="x", quantity=qty, destination_campus="Main", idempotency_key=f"dm{_n[0]}",
                                           submitted_at=at(d))
        if status:
            ResourceRequest.objects.filter(pk=r.pk).update(status=status)
        return r

    def months_of(self, per_month: dict):
        """per_month: {(year, month): [qty, ...]}"""
        for (y, m), qtys in per_month.items():
            for i, q in enumerate(qtys):
                self.req(date(y, m, 5 + i), q)

    def build(self, **kw):
        return forecast.build(unit_ids=None, today=TODAY, **kw)

    def test_too_few_records_is_insufficient(self):
        self.months_of({(2026, 8): [1], (2026, 9): [1], (2026, 10): [2]})
        fc = self.build()
        self.assertFalse(fc.enough)
        self.assertEqual(fc.reason, "records")
        self.assertIsNone(fc.total.baseline)

    def test_too_short_a_history_is_insufficient(self):
        self.months_of({(2026, 10): [1] * 12})
        fc = self.build()
        self.assertFalse(fc.enough)
        self.assertEqual(fc.reason, "months")

    def test_baseline_is_the_last_three_full_months_and_trend_compares_the_three_before(self):
        self.months_of({(2026, 5): [1, 1], (2026, 6): [1, 1], (2026, 7): [1, 1], (2026, 8): [3, 3], (2026, 9): [2, 2], (2026, 10): [2, 3]})
        self.req(date(2026, 11, 2), 9)  # current month: not used
        fc = self.build()
        self.assertTrue(fc.enough)
        self.assertEqual(fc.target, date(2026, 12, 1))
        self.assertEqual(fc.history_end, date(2026, 10, 31))
        self.assertEqual(fc.total.units[-3:], [6, 4, 5])
        self.assertAlmostEqual(fc.total.baseline, 5.0)
        self.assertEqual(fc.total.trend, "rising")  # 15 against 6
        self.assertEqual((fc.total.recent_low, fc.total.recent_high), (4, 6))
        self.assertEqual(fc.current_month_so_far, 9)

    def test_cancelled_requests_are_left_out(self):
        self.months_of({(2026, 8): [1] * 4, (2026, 9): [1] * 4, (2026, 10): [1] * 4})
        self.req(date(2026, 10, 20), 50, status=RequestStatus.CANCELLED)
        self.assertEqual(self.build().total.units[-1], 4)

    def test_category_rows_and_filter(self):
        self.months_of({(2026, 8): [1] * 4, (2026, 9): [1] * 4, (2026, 10): [1] * 4})
        for d in (date(2026, 8, 1), date(2026, 9, 1)):
            self.req(d, 5, category=self.chairs)
        fc = self.build()
        rows = {r.label: r for r in fc.rows}
        self.assertTrue(rows["Monitors"].enough)
        self.assertFalse(rows["Chairs"].enough)  # only 2 records: no number for that row
        self.assertEqual([r.label for r in self.build(category=self.chairs).rows], ["Chairs"])

    def test_scope_limits_the_requesting_units(self):
        self.months_of({(2026, 8): [1] * 4, (2026, 9): [1] * 4, (2026, 10): [1] * 4})
        self.assertEqual(forecast.build(unit_ids={self.w.cs.pk}, today=TODAY).records, 0)

    def test_optional_straight_line_is_compared_on_past_months(self):
        # Nov 2025 .. Oct 2026, one more unit each month
        self.months_of({(2025 + (10 + i) // 12, (10 + i) % 12 + 1): [1] * (i + 1) for i in range(12)})
        fc = self.build(compare=True)
        self.assertIsNotNone(fc.total.linear)
        self.assertIsNotNone(fc.total.mae_baseline)
        self.assertLess(fc.total.mae_linear, fc.total.mae_baseline)  # a steady rise: the line fits better
        ResourceRequest.objects.filter(submitted_at__lt=at(date(2026, 8, 1))).delete()  # now only 3 months
        self.assertIsNone(self.build(compare=True).total.linear)

    def test_sample_is_labelled_and_never_stored(self):
        before = ResourceRequest.objects.count()
        fc = self.build(sample=True)
        self.assertTrue(fc.sample)
        self.assertTrue(fc.enough)
        self.assertEqual(ResourceRequest.objects.count(), before)
        self.assertEqual(fc.total.units, self.build(sample=True).total.units)  # same sample every time

    def test_screen_permissions_and_wording(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("reporting:demand")).status_code, 403)
        self.client.force_login(self.officer)
        r = self.client.get(reverse("reporting:demand"))
        self.assertContains(r, "Insufficient data")
        r = self.client.get(reverse("reporting:demand"), {"sample": "1", "compare": "1"})
        self.assertContains(r, "Sample data.")
        self.assertContains(r, "never stored")
        self.assertContains(r, "Forecasts are estimates, not promises.")
        self.assertContains(r, "Past error")

    def test_arabic(self):
        self.client.force_login(self.officer)
        self.client.post(reverse("set_language"), {"language": "ar", "next": "/"})
        r = self.client.get(reverse("reporting:demand"), {"sample": "1"})
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "توقّع الطلب")
