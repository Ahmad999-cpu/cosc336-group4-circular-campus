"""Prices for the guest Pricing section.

The numbers come from apps.sustainability.calculator (MONTHLY_PRICE, VAT_RATE), the same table the
savings calculator uses, so the two can never disagree. Each visitor-facing institution type maps to one
of the calculator's three price groups. Charities and non-profits have no list price: they contact us
for a reduced price.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.utils.formats import number_format
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from apps.sustainability.calculator import MONTHLY_PRICE, VAT_RATE

# (key, label, calculator price group or None for "contact us")
TYPES = [
    ("university", _("Universities"), "asset_intensive"),
    ("hospital", _("Hospitals"), "asset_intensive"),
    ("school", _("Schools"), "medium"),
    ("hotel", _("Hotels"), "medium"),
    ("offices", _("Offices"), "low"),
    ("consultancy", _("Consultancies"), "low"),
    ("charity", _("Charities and non-profits"), None),
]
DEFAULT = "university"
BANDS = [_("Under 500 employees"), _("500–4,999 employees"), _("5,000–9,999 employees")]


def money(value: Decimal) -> str:
    """AED with grouping; two decimals only when there are fils (e.g. 1,102.50 with VAT)."""
    v = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    places = 0 if v == v.to_integral_value() else 2
    amount = number_format(v, places, force_grouping=True)
    return f"{amount} درهم" if (get_language() or "").startswith("ar") else f"AED {amount}"


def table():
    """{type key: [ {ex, inc} per band ] or None} with prices already formatted for the current language."""
    out = {}
    for key, _label, group in TYPES:
        if group is None:
            out[key] = None
            continue
        out[key] = [{"ex": money(Decimal(p)), "inc": money(Decimal(p) * (1 + VAT_RATE))} for _upper, p in MONTHLY_PRICE[group]]
    return out


def context(type_key: str | None, vat: bool):
    keys = [t[0] for t in TYPES]
    key = type_key if type_key in keys else DEFAULT
    data = table()
    rows = data[key]
    return {
        "types": [(k, label) for k, label, _g in TYPES],
        "type": key,
        "type_label": dict((k, label) for k, label, _g in TYPES)[key],
        "vat": vat,
        "vat_pct": int(VAT_RATE * 100),
        "cards": [{"band": b, "price": (rows[i]["inc"] if vat else rows[i]["ex"]) if rows else None} for i, b in enumerate(BANDS)],
        "data": data,
    }
