"""Public interface of the Sustainability module. OWNER: sustainability.

C7 dashboard: measures each shown with the formula and source next to it (Section 9.6).
Only locally selected carbon factors stored in EmissionFactor (with source and date) are used.
Missing inputs give None ("unavailable"), never 0 (FR-13.8, FR-15.10).
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.catalogue.models import Asset, Category
from apps.common.enums import Condition
from apps.resource_requests.models import RequestStatus, ResourceRequest
from apps.transfers.models import Transfer, TransferStatus

from .calculator import (LEAD_DAYS_OTHER_CAMPUS, LEAD_DAYS_SAME_CAMPUS, REPAIR_DAYS, REPAIR_SHARE_POOR,
                         TRANSFER_COST_OTHER_CAMPUS, TRANSFER_COST_SAME_CAMPUS)
from .models import EmissionFactor, ImpactType, SustainabilityImpact

ZERO = Decimal(0)


# ----------------------------------------------------------------------------- factors

def factor_for(category: Category) -> EmissionFactor | None:
    """Most specific locally selected factor: the category's own, else the nearest parent's (BR-15)."""
    node = category
    while node is not None:
        f = EmissionFactor.objects.filter(category=node).order_by("-source_date").first()
        if f is not None:
            return f
        node = node.parent
    return None


# ----------------------------------------------------------------------------- impacts

@transaction.atomic
def record_transfer_impact(transfer: Transfer, quantity: int | None = None) -> list[SustainabilityImpact]:
    """Called (through the transfer_received signal) when a receiver confirms. Idempotent per transfer.

    avoided purchase = units received x estimated value (verified when the unit confirmed a planned purchase
    was cancelled); carbon = units x kg CO2e per unit; waste diverted = units x typical mass per unit."""
    if transfer.impacts.exists():
        return list(transfer.impacts.all())
    units = quantity if quantity is not None else (transfer.received_quantity or transfer.quantity)
    asset = Asset.objects.select_related("category").get(pk=transfer.asset_id)
    out = []
    if asset.estimated_value is not None:
        verified = transfer.replaced_planned_purchase
        same = transfer.source_campus.strip().lower() == transfer.destination_campus.strip().lower()
        move = TRANSFER_COST_SAME_CAMPUS if same else TRANSFER_COST_OTHER_CAMPUS
        out.append(SustainabilityImpact(
            asset=asset, transfer=transfer, units=units,
            impact_type=ImpactType.VERIFIED_AVOIDED_PURCHASE if verified else ImpactType.AVOIDED_PURCHASE,
            avoided_cost=max(ZERO, asset.estimated_value * units - move), is_estimate=not verified,
            assumptions=f"{units} unit(s) × AED {asset.estimated_value:,.0f} estimated value − AED {move:,.0f} transfer"
                        + ("; the receiving unit confirmed a planned purchase was cancelled" if verified else "")))
    f = factor_for(asset.category)
    if f is not None:
        out.append(SustainabilityImpact(
            asset=asset, transfer=transfer, factor=f, units=units, impact_type=ImpactType.CARBON_REDUCTION,
            co2e_kg=f.kg_co2e_per_unit * units, is_estimate=True,
            assumptions=f"{units} unit(s) × {f.kg_co2e_per_unit} kg CO2e/{f.unit}; {f.source} ({f.source_date})"))
        if f.mass_kg_per_unit is not None:
            out.append(SustainabilityImpact(
                asset=asset, transfer=transfer, factor=f, units=units, impact_type=ImpactType.WASTE_DIVERSION,
                mass_kg=f.mass_kg_per_unit * units, is_estimate=True,
                assumptions=f"{units} unit(s) × {f.mass_kg_per_unit} kg typical mass; {f.source} ({f.source_date})"))
    SustainabilityImpact.objects.bulk_create(out)
    return out


# ----------------------------------------------------------------------------- dashboard (C7)

@dataclass
class Measure:
    key: str
    label: str
    value: Decimal | int | None  # None = unavailable
    unit: str
    formula: str
    source: str
    is_estimate: bool
    note: str = ""
    coverage: str = ""  # e.g. "8 of 10 units have a factor"


@dataclass
class Dashboard:
    measures: list[Measure]
    by_category: list[dict] = field(default_factory=list)
    by_month: list[dict] = field(default_factory=list)
    factors: list = field(default_factory=list)
    start: date | None = None
    end: date | None = None


def _bounds(start, end):
    tz = timezone.get_current_timezone()
    lo = timezone.make_aware(datetime.combine(start, time.min), tz) if start else None
    hi = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz) if end else None
    return lo, hi


def _completed(start=None, end=None, unit_ids=None):
    lo, hi = _bounds(start, end)
    qs = Transfer.objects.filter(status=TransferStatus.COMPLETED)
    if lo:
        qs = qs.filter(received_at__gte=lo)
    if hi:
        qs = qs.filter(received_at__lt=hi)
    if unit_ids:
        qs = qs.filter(Q(destination_department_id__in=unit_ids) | Q(source_department_id__in=unit_ids))
    return qs


def _round(x, places="1"):
    return x.quantize(Decimal(places), ROUND_HALF_UP) if x is not None else None


def dashboard_measures(user=None, period_start=None, period_end=None, unit_ids=None) -> Dashboard:
    """Five measures, each with formula and source; breakdowns by category and month; the factors used."""
    transfers = list(_completed(period_start, period_end, unit_ids).select_related("asset__category"))
    impacts = list(SustainabilityImpact.objects.filter(transfer__in=transfers).select_related("factor"))
    units = sum(t.received_quantity or 0 for t in transfers)

    def total(kind, attr):
        vals = [getattr(i, attr) for i in impacts if i.impact_type in kind and getattr(i, attr) is not None]
        return (sum(vals, ZERO) if vals else None), sum(i.units for i in impacts if i.impact_type in kind and getattr(i, attr) is not None)

    avoided, priced_units = total({ImpactType.AVOIDED_PURCHASE, ImpactType.VERIFIED_AVOIDED_PURCHASE}, "avoided_cost")
    verified, verified_units = total({ImpactType.VERIFIED_AVOIDED_PURCHASE}, "avoided_cost")
    co2e, carbon_units = total({ImpactType.CARBON_REDUCTION}, "co2e_kg")
    mass, mass_units = total({ImpactType.WASTE_DIVERSION}, "mass_kg")

    lo, hi = _bounds(period_start, period_end)
    reqs = ResourceRequest.objects.all()
    if lo:
        reqs = reqs.filter(submitted_at__gte=lo)
    if hi:
        reqs = reqs.filter(submitted_at__lt=hi)
    if unit_ids:
        reqs = reqs.filter(department_id__in=unit_ids)
    made = reqs.exclude(status=RequestStatus.CANCELLED).count()
    fulfilled = reqs.filter(status=RequestStatus.FULFILLED).count()

    def cov(n):
        return _("%(n)s of %(m)s units") % {"n": n, "m": units} if units else ""

    tx_source = _("Transfer records: units the receiving unit confirmed")
    measures = [
        Measure("units", _("Items reused"), units, _("units"), _("Σ units confirmed received in completed transfers"),
                tx_source, False),
        Measure("avoided", _("Purchases avoided"), _round(avoided), "AED",
                _("Σ (units received × the item's estimated value − transfer cost)"),
                _("Custodian's estimated value on each item record"), True,
                note=(_("AED %(v)s of this is verified: the receiving unit confirmed it cancelled a planned purchase.")
                      % {"v": f"{_round(verified):,}"}) if verified else _("None verified yet: no unit has confirmed a cancelled purchase."),
                coverage=cov(priced_units)),
        Measure("co2e", _("Carbon avoided"), _round(co2e), _("kg CO2e"),
                _("Σ units received × kg CO2e of making one new unit (transport emissions not yet subtracted)"),
                _("Locally selected carbon factors (see the table below)"), True,
                note="" if co2e is not None else _("Unavailable: no carbon factor covers the items moved."), coverage=cov(carbon_units)),
        Measure("waste", _("Waste diverted"), _round(mass), _("kg"), _("Σ units received × typical mass per unit"),
                _("Typical mass recorded with each locally selected factor"), True,
                note="" if mass is not None else _("Unavailable: no typical mass is recorded for the items moved."), coverage=cov(mass_units)),
        Measure("rate", _("Reuse rate"), round(100 * fulfilled / made) if made else None, "%",
                _("requests fulfilled by reuse ÷ requests made (cancelled ones excluded)"),
                _("Request records in the period"), False,
                note=_("%(f)s of %(m)s requests") % {"f": fulfilled, "m": made} if made else _("Unavailable: no requests in this period.")),
    ]

    cats: dict[str, dict] = {}
    for t in transfers:
        c = cats.setdefault(t.asset.category.name, {"category": t.asset.category.display_name, "units": 0, "aed": ZERO, "co2e": ZERO})
        c["units"] += t.received_quantity or 0
    for i in impacts:
        c = cats.get(next((t.asset.category.name for t in transfers if t.pk == i.transfer_id), ""), None)
        if c is None:
            continue
        if i.avoided_cost is not None:
            c["aed"] += i.avoided_cost
        if i.co2e_kg is not None:
            c["co2e"] += i.co2e_kg
    by_category = sorted(cats.values(), key=lambda c: (-c["units"], c["category"]))
    top = max((c["units"] for c in by_category), default=0)
    for c in by_category:
        c["share"] = round(100 * c["units"] / top) if top else 0

    months: "OrderedDict[str, int]" = OrderedDict()
    today = timezone.localdate()
    for k in range(5, -1, -1):
        y, m = today.year, today.month - k
        while m <= 0:
            y, m = y - 1, m + 12
        months[f"{y}-{m:02d}"] = 0
    for t in _completed(today.replace(day=1) - timedelta(days=160), None, unit_ids):
        key = timezone.localtime(t.received_at).strftime("%Y-%m")
        if key in months:
            months[key] += t.received_quantity or 0
    peak = max(months.values(), default=0)
    by_month = [{"month": datetime.strptime(k, "%Y-%m").date(), "units": v, "share": round(100 * v / peak) if peak else 0}
                for k, v in months.items()]

    used = {i.factor_id for i in impacts if i.factor_id}
    factors = list(EmissionFactor.objects.select_related("category").order_by("category__name"))
    for f in factors:
        f.used = f.pk in used
    return Dashboard(measures, by_category, by_month, factors, period_start, period_end)


# ----------------------------------------------------------------------------- net-cost comparison (bonus)

@dataclass
class NetCost:
    quantity: int
    buy_new: Decimal | None
    transport: Decimal
    storage: Decimal
    repair: Decimal
    reuse_total: Decimal
    avoided: Decimal | None
    avoided_pct: int | None
    co2e_kg: Decimal | None
    feasible: str          # "yes" | "repair" | "no"
    reasons: list[str]
    lead_days: int
    inputs: list[tuple[str, str]]

    @property
    def avoided_abs(self) -> Decimal | None:
        return abs(self.avoided) if self.avoided is not None else None

    @property
    def reuse_wins(self) -> bool | None:
        return None if self.avoided is None else self.avoided > 0


def net_cost_comparison(asset: Asset, quantity: int, new_unit_price=None, transport=None, storage=None, repair=None,
                        destination_campus: str = "", required_date: date | None = None) -> NetCost:
    """Bonus: feasibility and net cost of reusing this item instead of buying new.

    avoided = new unit price × quantity − (transport + storage + repair). Every input is listed and editable;
    defaults are the shared assumptions in calculator.py. Labelled an estimate on screen."""
    quantity = max(1, int(quantity))
    same_campus = bool(destination_campus) and destination_campus.strip().lower() == asset.location_campus.strip().lower()
    price = Decimal(new_unit_price) if new_unit_price not in (None, "") else asset.estimated_value
    t = Decimal(transport) if transport not in (None, "") else (TRANSFER_COST_SAME_CAMPUS if same_campus else TRANSFER_COST_OTHER_CAMPUS)
    s = Decimal(storage) if storage not in (None, "") else ZERO
    poor = asset.condition == Condition.POOR
    if repair not in (None, ""):
        r = Decimal(repair)
    else:
        r = (asset.estimated_value or ZERO) * quantity * REPAIR_SHARE_POOR if poor else ZERO
    buy_new = price * quantity if price is not None else None
    reuse = t + s + r
    avoided = buy_new - reuse if buy_new is not None else None
    pct = round(100 * avoided / buy_new) if buy_new else None

    free = asset.unreserved_quantity
    reasons, feasible = [], "yes"
    if free < quantity:
        feasible = "no"
        reasons.append(_("Only %(n)s free; you need %(q)s.") % {"n": free, "q": quantity})
    if asset.lifecycle_state in ("UNDER_MAINTENANCE", "RETIRED", "DONATED", "RECYCLED", "DISPOSED"):
        feasible = "no"
        reasons.append(_("The item is %(s)s.") % {"s": asset.get_lifecycle_state_display().lower()})
    lead = LEAD_DAYS_SAME_CAMPUS if same_campus or not destination_campus else LEAD_DAYS_OTHER_CAMPUS
    if poor and feasible != "no":
        feasible = "repair"
        lead += REPAIR_DAYS
        reasons.append(_("Condition is Poor: plan a repair first."))
    if required_date and feasible != "no" and (required_date - timezone.localdate()).days < lead:
        reasons.append(_("Probably not ready by %(d)s (about %(n)s days).") % {"d": required_date.strftime("%d %b"), "n": lead})
    if avoided is not None and avoided <= 0:
        reasons.append(_("Buying new is cheaper with these inputs."))

    f = factor_for(asset.category)
    inputs = [
        (_("New price per unit"), f"AED {price:,.0f}" + ("" if new_unit_price not in (None, "") else _(" (item's estimated value)")) if price is not None else _("unknown")),
        (_("Transport"), f"AED {t:,.0f}" + ("" if transport not in (None, "") else (_(" (same campus)") if same_campus else _(" (between campuses)")))),
        (_("Storage"), f"AED {s:,.0f}"),
        (_("Repair"), f"AED {r:,.0f}" + (_(" (Poor condition: repair at 20%)") if poor and repair in (None, "") else "")),
    ]
    return NetCost(quantity, buy_new, t, s, r, reuse, avoided, pct, f.kg_co2e_per_unit * quantity if f else None,
                   feasible, reasons, lead, inputs)
