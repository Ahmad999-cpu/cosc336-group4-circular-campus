"""C7 dashboard, the public savings calculator, and the reuse-or-buy-new comparison (bonus features)."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.catalogue.models import Asset

from . import calculator, services

PERIODS = [("30", _("Last 30 days")), ("term", _("This term")), ("year", _("This year")), ("all", _("All time"))]
TYPES = [("asset_intensive", _("Universities, hospitals, labs")), ("medium", _("Schools, hotels, government")),
         ("low", _("Offices, consultancies"))]
PARTS = [("conservative", _("Cautious (6%)")), ("typical", _("Typical (12%)")), ("high", _("High (18%)"))]


def _period(key: str):
    today = timezone.localdate()
    if key == "30":
        return today - timedelta(days=29), today
    if key == "term":  # KU terms: Spring Jan-May, Summer Jun-Aug, Fall Aug-Dec
        start = date(today.year, 8, 15) if today.month >= 8 and (today.month, today.day) >= (8, 15) else (
            date(today.year, 6, 1) if today.month >= 6 else date(today.year, 1, 1))
        return start, today
    if key == "year":
        return date(today.year, 1, 1), today
    return None, None


@login_required
def dashboard(request):
    key = request.GET.get("period", "term")
    if key not in dict(PERIODS):
        key = "term"
    start, end = _period(key)
    d = services.dashboard_measures(request.user, start, end)
    return render(request, "sustainability/dashboard.html", {"d": d, "periods": PERIODS, "period": key,
                                                            "hero": d.measures[0], "rest": d.measures[1:]})


def _int(v, default, lo, hi):
    try:
        return max(lo, min(hi, int(str(v).replace(",", ""))))
    except (TypeError, ValueError):
        return default


def calculator_page(request):
    """Public (no sign-in): what could an institution save? One formula, in calculator.py."""
    kind = request.GET.get("type") if request.GET.get("type") in calculator.SAVINGS_PER_ACTIVE_USER else "asset_intensive"
    part = request.GET.get("part") if request.GET.get("part") in calculator.PARTICIPATION else "typical"
    staff = _int(request.GET.get("staff"), 1000, 1, 100000)
    e = calculator.estimate_savings(kind, staff, part)
    price = calculator.monthly_price(kind, staff)
    top = max(e.annual_savings, e.annual_subscription or 0) or 1
    ctx = {"types": TYPES, "parts": PARTS, "kind": kind, "part": part, "staff": staff, "e": e, "monthly": price,
           "savings_w": round(100 * e.annual_savings / top), "cost_w": round(100 * (e.annual_subscription or 0) / top),
           "per_user": calculator.SAVINGS_PER_ACTIVE_USER[kind],
           "ret_text": f"{e.return_multiple.normalize():f}" if e.return_multiple is not None else "", "rate": int(calculator.PARTICIPATION[part] * 100),
           "price_table": [(label, calculator.MONTHLY_PRICE[k]) for k, label in TYPES]}
    if request.headers.get("HX-Target") == "calc-out":
        return render(request, "sustainability/_calc_out.html", ctx)
    # Visitors see it inside the guest site (its header and menu); signed-in people inside the app.
    ctx["base_template"] = "base.html" if request.user.is_authenticated else "guest/base.html"
    ctx["page"] = "calculator"
    return render(request, "sustainability/calculator.html", ctx)


def _dec(v):
    if v in (None, ""):
        return None
    try:
        d = Decimal(str(v).replace(",", ""))
        return d if d >= 0 else None
    except InvalidOperation:
        return None


@login_required
def compare(request, pk):
    """Reuse or buy new? Feasibility and net cost for one item, with every input editable."""
    asset = get_object_or_404(Asset.objects.select_related("category", "owner_department"), pk=pk)
    from apps.catalogue.services import can_view
    if not can_view(request.user, asset):  # found while adding Feature 3: this page did not check visibility
        raise Http404()
    me = request.user.department
    g = request.GET
    qty = _int(g.get("qty"), 1, 1, 999)
    campus = g.get("campus", (me.campus if me and me.campus else "")) or ""
    required = None
    if g.get("needed_by"):
        try:
            required = date.fromisoformat(g["needed_by"])
        except ValueError:
            required = None
    nc = services.net_cost_comparison(asset, qty, _dec(g.get("price")), _dec(g.get("transport")), _dec(g.get("storage")),
                                      _dec(g.get("repair")), destination_campus=campus, required_date=required)
    top = max(nc.buy_new or 0, nc.reuse_total) or 1
    ctx = {"a": asset, "nc": nc, "qty": qty, "campus": campus, "g": g, "needed_by": g.get("needed_by", ""),
           "new_w": round(100 * (nc.buy_new or 0) / top), "reuse_w": max(2, round(100 * nc.reuse_total / top))}
    if request.headers.get("HX-Target") == "nc-out":
        return render(request, "sustainability/_compare_out.html", ctx)
    return render(request, "sustainability/_compare.html", ctx)


def _advice_asset(request, pk):
    from . import advice
    asset = get_object_or_404(Asset.objects.select_related("category", "owner_department", "custodian"), pk=pk)
    if not advice.can_advise(request.user, asset):
        raise Http404()
    return asset


@login_required
def advice_panel(request, pk):
    """Feature 2: the sustainable-action recommendation for one asset. Read-only: viewing changes nothing."""
    from . import advice
    asset = _advice_asset(request, pk)
    ctx = {"adv": advice.recommend(request.user, asset), "a": asset}
    if request.headers.get("HX-Request"):
        return render(request, "sustainability/_advice.html", ctx)
    return render(request, "sustainability/advice_page.html", ctx)


@login_required
@require_POST
def advice_ai(request, pk):
    """Feature 2 (optional): ask the AI gateway to re-word the advice. Labelled; falls back to the rules."""
    from . import advice
    asset = _advice_asset(request, pk)
    return render(request, "sustainability/_advice_ai.html",
                  {"ai": advice.explain_with_ai(request.user, asset, get_language() or "en"), "a": asset})
