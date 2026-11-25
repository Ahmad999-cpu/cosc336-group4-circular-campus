"""Reports screen (C9) and AI summary review (AI feature 5)."""
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.permissions import units_for
from apps.common.errors import DomainError
from apps.web.htmx import with_toast

from . import services
from .forms import ReportFilter
from .models import ReportType

SCREEN_ROWS = 100  # the page shows the newest 100; the CSV has every row


def _filters(request, data):
    form = ReportFilter(data, user=request.user)
    if form.is_bound:
        form.is_valid()
    return form, form.filters()


def _panel_ctx(request, f, outcome=None):
    published_, draft = services.summaries_for(request.user, f)
    can_publish = units_for(request.user, "reports.publish").exists()
    unchecked = outcome.unchecked if outcome else []
    if draft is not None and not outcome:
        _cols, _rows, totals = services.build(request.user, f)
        unchecked = services.unchecked_numbers(draft.draft_text, totals, f)
    return {"published": published_, "draft": draft, "can_publish": can_publish, "f": f, "unchecked": unchecked,
            "outcome": outcome, "query": urlencode({k: v for k, v in f.as_dict().items() if v})}


@needs("reports.view")
def index(request):
    form, f = _filters(request, request.GET if request.GET else None)
    cols, rows, totals = services.build(request.user, f)
    ctx = {"form": form, "f": f, "cols": [(c, services.COLUMN_LABELS.get(c, c)) for c in cols], "rows": rows[:SCREEN_ROWS],
           "row_count": len(rows), "totals": totals, "is_rt": f.report_type == ReportType.REQUESTS_TRANSFERS,
           "csv_url": csv_url(f), "num_cols": {"quantity", "free_units", "estimated_value_aed"},
           "date_cols": {"submitted_at", "dispatched_at", "received_at", "request_id"}, **_panel_ctx(request, f)}
    if request.headers.get("HX-Target") == "report-body":  # filters changed: only the body is swapped
        return render(request, "reporting/_body.html", ctx)
    return render(request, "reporting/index.html", ctx)


@needs("reports.view")
def csv_export(request):
    form, f = _filters(request, request.GET)
    name, body = services.export_csv(request.user, f)
    resp = HttpResponse(body, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp


@needs("reports.view")
@require_POST
def summarize(request):
    form, f = _filters(request, request.POST)
    outcome = services.generate_summary(request.user, f)
    resp = render(request, "reporting/_summary.html", _panel_ctx(request, f, outcome))
    if outcome.summary is None:
        return with_toast(resp, outcome.message, ok=False)
    return with_toast(resp, _("Draft ready. Check it, edit it, then publish."))


@needs("reports.view")
@require_POST
def publish(request, pk):
    form, f = _filters(request, request.POST)
    try:
        services.publish_summary(request.user, pk, request.POST.get("text", ""))
    except DomainError as e:
        ctx = _panel_ctx(request, f)
        ctx["error"] = str(e)
        return render(request, "reporting/_summary.html", ctx)
    return with_toast(render(request, "reporting/_summary.html", _panel_ctx(request, f)), _("Summary published."))


@needs("reports.view")
@require_POST
def discard(request, pk):
    form, f = _filters(request, request.POST)
    services.discard_summary(request.user, pk)
    return with_toast(render(request, "reporting/_summary.html", _panel_ctx(request, f)), _("Draft discarded."))


def csv_url(f) -> str:
    return reverse("reporting:csv") + "?" + urlencode({k: v for k, v in f.as_dict().items() if v})


@needs("reports.view")
def demand(request):
    """Feature 4: demand forecast by category, from real request records (or a labelled sample)."""
    from apps.catalogue.models import Category

    from . import forecast
    g = request.GET
    units = units_for(request.user, "reports.view")
    unit = units.filter(pk=g.get("unit")).first() if len(g.get("unit", "")) == 36 else None
    category = Category.objects.filter(pk=g.get("category")).first() if len(g.get("category", "")) == 36 else None
    ids = services.scope(request.user, services.Filters(unit_id=str(unit.pk) if unit else ""))
    fc = forecast.build(unit_ids=ids, category=category, compare=g.get("compare") == "1", sample=g.get("sample") == "1")
    ctx = {"fc": fc, "units": units, "unit": unit, "categories": Category.objects.order_by("name"), "category": category,
           "compare": g.get("compare") == "1", "sample": fc.sample, "min_records": forecast.MIN_RECORDS,
           "min_months": forecast.MIN_MONTHS, "min_cat": forecast.MIN_CATEGORY_RECORDS, "band": int(forecast.TREND_BAND * 100),
           "linear_min": forecast.LINEAR_MIN_MONTHS}
    if request.headers.get("HX-Target") == "demand-body":
        return render(request, "reporting/_demand_body.html", ctx)
    return render(request, "reporting/demand.html", ctx)
