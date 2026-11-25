"""Feature 4: demand forecast by asset category, from real request records.

Method (deliberately simple, shown on screen):
  demand in a month   = units asked for in requests sent that month (cancelled requests excluded)
  baseline forecast   = average of the last 3 full months
  trend               = last 3 full months against the 3 before: rising (> +20 %), falling (< -20 %), steady
  optional comparison = a straight-line trend over up to 12 months, scored against the baseline on past months
                        (one-step-ahead, mean absolute error). It is only offered with 9+ months of history.
Not enough data (fewer than MIN_RECORDS requests or fewer than MIN_MONTHS months since the first one) gives an
"insufficient data" answer instead of a number. Forecasts are for categories and units, never for people.

Sample mode builds a labelled, made-up series in memory for demonstrations. It is never written to the database.
"""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.catalogue.models import Category
from apps.resource_requests.models import RequestStatus, ResourceRequest

HISTORY_MONTHS = 12
BASELINE_MONTHS = 3
MIN_RECORDS = 10          # whole selection
MIN_MONTHS = 3            # months since the first request in the selection
MIN_CATEGORY_RECORDS = 3  # per category row, in the history window
TREND_BAND = 0.20
LINEAR_MIN_MONTHS = 9


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return date(y, m + 1, 1)


@dataclass
class Series:
    key: str                       # category id or "all"
    label: str
    months: list[date]
    units: list[int]
    records: int
    enough: bool
    baseline: float | None = None
    recent_low: int | None = None
    recent_high: int | None = None
    trend: str | None = None       # "rising" | "falling" | "steady" | None
    linear: float | None = None
    mae_baseline: float | None = None
    mae_linear: float | None = None

    @property
    def peak(self) -> int:
        return max(self.units + [round(self.baseline or 0), round(self.linear or 0), 1])

    @property
    def bars(self):
        p = self.peak
        return [(m, u, round(100 * u / p)) for m, u in zip(self.months, self.units)]

    @property
    def forecast_pct(self) -> int:
        return round(100 * (self.baseline or 0) / self.peak)


@dataclass
class Forecast:
    history_start: date
    history_end: date              # last day of the last full month
    target: date                   # first day of the forecast month
    records: int
    first_record: date | None
    enough: bool
    total: Series
    rows: list[Series] = field(default_factory=list)
    sample: bool = False
    current_month_so_far: int = 0
    reason: str = ""               # why it is insufficient


def _baseline(units: list[int]) -> float:
    last = units[-BASELINE_MONTHS:]
    return sum(last) / len(last)


def _linear_next(units: list[int]) -> float:
    n = len(units)
    xs = range(n)
    mx, my = (n - 1) / 2, sum(units) / n
    var = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, units)) / var if var else 0.0
    return max(0.0, my + slope * (n - mx))


def _backtest(units: list[int]) -> tuple[float | None, float | None]:
    """One-step-ahead on the history: predict month t from months before t. Mean absolute error of each method."""
    errs_b, errs_l = [], []
    for t in range(6, len(units)):
        past, actual = units[:t], units[t]
        errs_b.append(abs(_baseline(past) - actual))
        errs_l.append(abs(_linear_next(past) - actual))
    if len(errs_b) < 3:
        return None, None
    return sum(errs_b) / len(errs_b), sum(errs_l) / len(errs_l)


def _fill(s: Series, compare: bool) -> Series:
    """compare: the caller already checked there are LINEAR_MIN_MONTHS of history."""
    if not s.enough:
        return s
    s.baseline = _baseline(s.units)
    recent = s.units[-BASELINE_MONTHS:]
    s.recent_low, s.recent_high = min(recent), max(recent)
    before = s.units[-2 * BASELINE_MONTHS:-BASELINE_MONTHS]
    if sum(before) > 0:
        change = (sum(recent) - sum(before)) / sum(before)
        s.trend = "rising" if change > TREND_BAND else "falling" if change < -TREND_BAND else "steady"
    elif sum(recent) > 0:
        s.trend = "rising"
    if compare:
        s.linear = _linear_next(s.units)
        s.mae_baseline, s.mae_linear = _backtest(s.units)
    return s


def build(*, unit_ids: set | None, category: Category | None = None, compare: bool = False, today: date | None = None,
          sample: bool = False) -> Forecast:
    """unit_ids: the requesting units in scope (from reporting.services.scope). category: narrow to a subtree."""
    today = today or timezone.localdate()
    this_month = today.replace(day=1)
    start = add_months(this_month, -HISTORY_MONTHS)
    months = [add_months(start, i) for i in range(HISTORY_MONTHS)]
    target = add_months(this_month, 1)

    if sample:
        counts, first, so_far = _sample(months, category)
    else:
        qs = ResourceRequest.objects.exclude(status=RequestStatus.CANCELLED)
        if unit_ids is not None:
            qs = qs.filter(department_id__in=unit_ids)
        if category is not None:
            qs = qs.filter(category_id__in=category.descendant_ids())
        tz = timezone.get_current_timezone()
        first_dt = qs.order_by("submitted_at").values_list("submitted_at", flat=True).first()
        first = timezone.localtime(first_dt).date() if first_dt else None
        rows = (qs.filter(submitted_at__date__gte=start, submitted_at__date__lt=this_month)
                .annotate(m=TruncMonth("submitted_at", tzinfo=tz)).values("m", "category_id").annotate(units=Sum("quantity"), n=Count("id")))
        cats = {c.pk: c for c in Category.objects.select_related("parent")}
        counts = defaultdict(lambda: {"units": defaultdict(int), "records": 0, "label": ""})
        for r in rows:
            root = cats.get(r["category_id"])  # the category the request was made in (e.g. Monitors)
            key = str(root.pk) if root else "?"
            m = r["m"].date() if hasattr(r["m"], "date") else r["m"]
            counts[key]["units"][m.replace(day=1)] += r["units"] or 0
            counts[key]["records"] += r["n"] or 0
            counts[key]["label"] = root.display_name if root else "?"
        so_far = qs.filter(submitted_at__date__gte=this_month).aggregate(u=Sum("quantity"))["u"] or 0

    total_units = [sum(c["units"].get(m, 0) for c in counts.values()) for m in months]
    records = sum(c["records"] for c in counts.values())
    months_known = 0 if first is None else (this_month.year - first.year) * 12 + this_month.month - first.month
    reason = ""
    if records < MIN_RECORDS:
        reason = "records"
    elif months_known < MIN_MONTHS:
        reason = "months"
    enough = not reason
    compare = compare and months_known >= LINEAR_MIN_MONTHS
    total = _fill(Series("all", "", months, total_units, records, enough), compare)
    out_rows = []
    for key, c in sorted(counts.items(), key=lambda kv: -sum(kv[1]["units"].values())):
        units = [c["units"].get(m, 0) for m in months]
        s = Series(key, c["label"], months, units, c["records"], enough and c["records"] >= MIN_CATEGORY_RECORDS)
        out_rows.append(_fill(s, compare))
    return Forecast(start, this_month - timedelta(days=1), target, records, first, enough, total,
                    out_rows, sample, so_far, reason)


# ----------------------------------------------------------------------------- sample data (never stored)

SAMPLE = {  # category name: base units per month, noise, trend per month. Made up for the demo.
    "Monitors": (14, 6, 0.6), "Chairs": (22, 10, 0.0), "Oscilloscopes": (6, 3, -0.2), "Projectors": (3, 1, 0.1),
}


def _sample(months: list[date], category: Category | None):
    rnd = random.Random(336)  # fixed seed: the same sample every time
    counts = {}
    for name, (base, swing, slope) in SAMPLE.items():
        if category is not None:
            c = Category.objects.filter(name=name).first()
            if c is None or c.pk not in category.descendant_ids():
                continue
        units = {}
        for i, m in enumerate(months):
            term = 1.6 if m.month in (1, 2, 8, 9) else 0.7 if m.month in (6, 7) else 1.0  # semester starts / summer
            units[m] = max(0, round((base + slope * i) * term + rnd.uniform(-swing, swing) / 2))
        c = Category.objects.filter(name=name).first()
        counts[name] = {"units": units, "records": max(1, sum(units.values()) // 2), "label": c.display_name if c else name}
    return counts, months[0], 0
