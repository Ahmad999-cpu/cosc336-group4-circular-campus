"""Public interface of the Reporting module. OWNER: reporting.

C9 basic report and AI feature 5 (required): the database computes every number; the AI only writes
a draft paragraph from those numbers; a person edits it before publishing (FR-15.13, Section 9.10).
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from apps.access.permissions import units_for
from apps.ai.gateway import AIGateway
from apps.ai.models import AIOutcome, ModelVersion
from apps.audit.services import record
from apps.catalogue.models import Asset, AssetState
from apps.catalogue.services import published
from apps.common.errors import Forbidden, ValidationFailed
from apps.resource_requests.models import RequestStatus, ResourceRequest
from apps.transfers.models import Transfer, TransferStatus

from .models import AISummary, Report, ReportType, SummaryStatus

MAX_AI_ROWS = 200  # Section 9.10: the AI sees the totals and at most 200 rows

REQUESTS_TRANSFERS_COLUMNS = [
    "request_id", "submitted_at", "department", "category", "quantity", "status",
    "asset", "approved_by", "transfer_status", "dispatched_at", "received_at",
]
AVAILABLE_ASSETS_COLUMNS = ["asset_id", "name", "category", "department", "campus", "free_units", "condition",
                            "estimated_value_aed"]
COLUMN_LABELS = {
    "request_id": _("Request"), "submitted_at": _("Sent"), "department": _("Unit"), "category": _("Category"),
    "quantity": _("Qty"), "status": _("Status"), "asset": _("Item"), "approved_by": _("Decided by"),
    "transfer_status": _("Transfer"), "dispatched_at": _("Dispatched"), "received_at": _("Received"),
    "asset_id": _("Item ID"), "name": _("Item"), "campus": _("Campus"), "free_units": _("Free"),
    "condition": _("Condition"), "estimated_value_aed": _("Value (AED)"),
}
TYPES = {ReportType.REQUESTS_TRANSFERS: REQUESTS_TRANSFERS_COLUMNS, ReportType.AVAILABLE_ASSETS: AVAILABLE_ASSETS_COLUMNS}
# Columns that name a person: shown to people with reports.view, never sent to the AI (FR-1.5).
PERSONAL_COLUMNS = {"approved_by"}


# ----------------------------------------------------------------------------- filters

@dataclass
class Filters:
    report_type: str = ReportType.REQUESTS_TRANSFERS
    start: date | None = None
    end: date | None = None
    unit_id: str = ""

    @classmethod
    def default(cls, report_type=ReportType.REQUESTS_TRANSFERS):
        today = timezone.localdate()
        return cls(report_type, today - timedelta(days=29), today, "")

    def as_dict(self) -> dict:
        return {"type": self.report_type, "start": self.start.isoformat() if self.start else "",
                "end": self.end.isoformat() if self.end else "", "unit": str(self.unit_id or "")}

    def bounds(self):
        tz = timezone.get_current_timezone()
        lo = timezone.make_aware(datetime.combine(self.start, time.min), tz) if self.start else None
        hi = timezone.make_aware(datetime.combine(self.end + timedelta(days=1), time.min), tz) if self.end else None
        return lo, hi


def scope(user, f: Filters):
    """Units this person may report on, narrowed to the chosen unit and its children."""
    units = units_for(user, "reports.view")
    if not units.exists():
        raise Forbidden("Not permitted: reports.view")
    ids = set(units.values_list("pk", flat=True))
    if f.unit_id:
        from apps.access.models import Department
        chosen = Department.objects.filter(pk=f.unit_id).first()
        if chosen is None or chosen.pk not in ids:
            raise Forbidden("You can't report on that unit")
        subtree, frontier = {chosen.pk}, [chosen.pk]
        while frontier:
            frontier = list(Department.objects.filter(parent_id__in=frontier).exclude(pk__in=subtree).values_list("pk", flat=True))
            subtree.update(frontier)
        ids &= subtree
    return ids


def _fmt(dt) -> str:
    return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M") if dt else ""


# ----------------------------------------------------------------------------- C9 rows

def _request_qs(user, f: Filters):
    ids = scope(user, f)
    lo, hi = f.bounds()
    qs = ResourceRequest.objects.filter(Q(department_id__in=ids) | Q(selected_asset__owner_department_id__in=ids))
    if lo:
        qs = qs.filter(submitted_at__gte=lo)
    if hi:
        qs = qs.filter(submitted_at__lt=hi)
    return qs.select_related("department", "category", "selected_asset", "decision__reviewer").order_by("-submitted_at")


def requests_transfers_rows(user, f: Filters) -> list[dict]:
    """C9: one row per request with its latest transfer (if any)."""
    reqs = list(_request_qs(user, f))
    transfers = {}
    for t in Transfer.objects.filter(request__in=reqs).order_by("reservation__created_at"):
        transfers[t.request_id] = t  # latest wins
    rows = []
    for r in reqs:
        t = transfers.get(r.pk)
        decision = getattr(r, "decision", None)
        rows.append({
            "request_id": str(r.pk)[:8], "submitted_at": _fmt(r.submitted_at), "department": r.department.name,
            "category": r.category.name, "quantity": r.quantity, "status": r.get_status_display(),
            "asset": r.selected_asset.name if r.selected_asset else "", "approved_by": decision.reviewer.full_name if decision else "",
            "transfer_status": t.get_status_display() if t else "", "dispatched_at": _fmt(t.dispatched_at) if t else "",
            "received_at": _fmt(t.received_at) if t else "",
        })
    return rows


def requests_transfers_totals(user, f: Filters) -> dict:
    """Every number on the page and in the AI's input, computed by the database (FR-15.13)."""
    qs = _request_qs(user, f)
    by_status = dict(qs.order_by().values("status").annotate(n=Count("pk")).values_list("status", "n"))
    approved = by_status.get(RequestStatus.APPROVED, 0) + by_status.get(RequestStatus.FULFILLED, 0)
    rejected = by_status.get(RequestStatus.REJECTED, 0)
    hours = [(r.decision.decided_at - r.submitted_at).total_seconds() / 3600
             for r in qs.filter(decision__isnull=False).select_related("decision")]
    done = Transfer.objects.filter(request__in=qs, status=TransferStatus.COMPLETED).select_related("asset")
    units_moved = sum(t.received_quantity or 0 for t in done)
    value = sum((t.asset.estimated_value or Decimal(0)) * (t.received_quantity or 0) for t in done)
    top = list(qs.order_by().values("category__name").annotate(n=Count("pk")).order_by("-n", "category__name")[:3])
    return {
        "requests": qs.count(),
        "units_requested": qs.aggregate(s=Sum("quantity"))["s"] or 0,
        "pending": by_status.get(RequestStatus.PENDING_APPROVAL, 0),
        "approved": approved,
        "rejected": rejected,
        "cancelled": by_status.get(RequestStatus.CANCELLED, 0),
        "approval_rate_pct": round(100 * approved / (approved + rejected)) if (approved + rejected) else None,
        "median_hours_to_decision": round(statistics.median(hours), 1) if hours else None,
        "transfers_completed": done.count(),
        "transfers_in_transit": Transfer.objects.filter(request__in=qs, status=TransferStatus.IN_TRANSIT).count(),
        "units_moved": units_moved,
        "value_reused_aed": int(value.quantize(Decimal("1"))) if value else 0,
        "replaced_planned_purchases": done.filter(replaced_planned_purchase=True).count(),
        "top_categories": [{"category": t["category__name"], "requests": t["n"]} for t in top],
    }


# ----------------------------------------------------------------------------- available assets

def _assets_qs(user, f: Filters):
    ids = scope(user, f)
    return (published().filter(owner_department_id__in=ids).select_related("category", "owner_department")
            .order_by("category__name", "name"))


def available_assets_rows(user, f: Filters) -> list[dict]:
    return [{"asset_id": str(a.pk)[:8], "name": a.name, "category": a.category.name, "department": a.owner_department.name,
             "campus": a.location_campus, "free_units": a.unreserved_quantity, "condition": a.get_condition_display(),
             "estimated_value_aed": int(a.estimated_value) if a.estimated_value is not None else ""}
            for a in _assets_qs(user, f)]


def available_assets_totals(user, f: Filters) -> dict:
    assets = list(_assets_qs(user, f))
    return {
        "items": len(assets),
        "free_units": sum(a.unreserved_quantity for a in assets),
        "value_free_aed": int(sum((a.estimated_value or 0) * a.unreserved_quantity for a in assets)),
        "units_with_listings": len({a.owner_department_id for a in assets}),
        "under_maintenance": Asset.objects.filter(owner_department_id__in=scope(user, f), lifecycle_state=AssetState.UNDER_MAINTENANCE).count(),
    }


def build(user, f: Filters) -> tuple[list[str], list[dict], dict]:
    """(columns, rows, totals) for the screen and the CSV: one function, so they can't disagree (D5)."""
    if f.report_type == ReportType.AVAILABLE_ASSETS:
        return AVAILABLE_ASSETS_COLUMNS, available_assets_rows(user, f), available_assets_totals(user, f)
    if f.report_type == ReportType.REQUESTS_TRANSFERS:
        return REQUESTS_TRANSFERS_COLUMNS, requests_transfers_rows(user, f), requests_transfers_totals(user, f)
    raise ValidationFailed("Unknown report type")


@transaction.atomic
def export_csv(user, f: Filters) -> tuple[str, str]:
    """C9 CSV: same columns and rows as the screen. Records the export (who, when, filters)."""
    cols, rows, _totals = build(user, f)
    rep = Report.objects.create(generated_by=user, report_type=f.report_type, filters=f.as_dict(),
                                period_start=f.start, period_end=f.end)
    rep.mark_exported()
    record(user, "export_report", "Report", rep.pk, after={"rows": len(rows), **f.as_dict()})
    name = f"circular-campus-{f.report_type.lower().replace('_', '-')}-{f.start or 'all'}-{f.end or 'now'}.csv"
    return name, "﻿" + Report.to_csv(cols, rows)  # BOM so Excel opens Arabic text correctly


# ----------------------------------------------------------------------------- AI feature 5

NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")


def allowed_numbers(totals: dict, f: Filters) -> set[str]:
    """Numbers a summary may mention: every total, and the dates of the period."""
    out: set[str] = set()

    def add(v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float, Decimal)):
            d = Decimal(str(v))
            out.add(f"{d.normalize():f}")
            out.add(f"{int(d)}" if d == int(d) else f"{d:.1f}")
        elif isinstance(v, dict):
            for x in v.values():
                add(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                add(x)

    add(totals)
    for d in (f.start, f.end):
        if d:
            out.update({str(d.year), str(d.day), f"{d.day:02d}", str(d.month)})
    if f.start and f.end:
        out.add(str((f.end - f.start).days + 1))
    return out


def unchecked_numbers(text: str, totals: dict, f: Filters) -> list[str]:
    """Numbers in a summary that are not in the report: shown to the editor to check (FR-15.13)."""
    ok = allowed_numbers(totals, f)
    found = []
    for m in NUMBER.findall(text or ""):
        n = m.replace(",", "")
        n = f"{Decimal(n).normalize():f}" if n.replace(".", "").isdigit() else n
        if n not in ok and n not in found:
            found.append(m)
    return found


def summary_input(user, f: Filters) -> dict:
    """ReportContent sent to the AI: type, period, totals, at most 200 rows without names, limitations."""
    cols, rows, totals = build(user, f)
    safe_cols = [c for c in cols if c not in PERSONAL_COLUMNS]
    limitations = [str(_("Only units the person who generated the report can see are included."))]
    if len(rows) > MAX_AI_ROWS:
        limitations.append(f"Only the {MAX_AI_ROWS} most recent rows are included; totals cover all {len(rows)} rows.")
    if f.report_type == ReportType.REQUESTS_TRANSFERS:
        limitations.append("Value reused uses each item's estimated value, not a purchase price.")
    return {"report_type": f.report_type, "language": (get_language() or "en")[:2],
            "period": {"start": f.as_dict()["start"], "end": f.as_dict()["end"]},
            "totals": totals, "rows": [{c: r[c] for c in safe_cols} for r in rows[:MAX_AI_ROWS]],
            "row_count": len(rows), "limitations": limitations}


@dataclass
class SummaryOutcome:
    summary: AISummary | None
    status: str
    message: str = ""
    unchecked: list = field(default_factory=list)


@transaction.atomic
def generate_summary(user, f: Filters, gateway: AIGateway | None = None) -> SummaryOutcome:
    """AI feature 5. The report is saved first (period + data cut-off), then the AI drafts text from its totals.
    If the AI is unavailable or slow, the report still works and the screen says so (FR-15.14)."""
    scope(user, f)
    if not _can_publish_somewhere(user):
        raise Forbidden("Not permitted: reports.publish")
    payload = summary_input(user, f)
    rep = Report.objects.create(generated_by=user, report_type=f.report_type, filters=f.as_dict(),
                                period_start=f.start, period_end=f.end)
    result = (gateway or AIGateway()).summarize(payload, user)
    if not result.ok or not isinstance(result.value, dict) or not (result.value.get("text") or "").strip():
        msg = {AIOutcome.TIMEOUT: _("The AI took too long. The numbers above are complete; try the summary again later."),
               AIOutcome.UNAVAILABLE: _("No AI summary is available right now. The numbers above are complete.")}
        return SummaryOutcome(None, result.status, str(msg.get(result.status, _("The AI couldn't write a summary this time."))))
    text = result.value["text"].strip()
    mv = ModelVersion.objects.get(pk=result.model_version_id)
    s = AISummary.objects.create(report=rep, model_version=mv, draft_text=text, final_text=text)
    record(user, "ai_summary_draft", "AISummary", s.pk, after={"report": str(rep.pk), "inference": str(result.inference_id)})
    return SummaryOutcome(s, result.status, unchecked=unchecked_numbers(text, payload["totals"], f))


def _can_publish_somewhere(user) -> bool:
    return units_for(user, "reports.publish").exists()


def _summary_for(user, summary_id) -> AISummary:
    s = AISummary.objects.select_related("report").get(pk=summary_id)
    if not _can_publish_somewhere(user):
        raise Forbidden("Not permitted: reports.publish")
    if s.report.generated_by_id != user.pk and not units_for(user, "reports.publish").filter(parent__isnull=True).exists():
        raise Forbidden("Only the person who generated this draft, or an institution-wide editor, can publish it")
    return s


@transaction.atomic
def publish_summary(user, summary_id, text: str) -> AISummary:
    s = _summary_for(user, summary_id)
    text = (text or "").strip()
    if len(text) < 20:
        raise ValidationFailed("Write at least a sentence before publishing")
    s.accept(text[:4000], user)
    record(user, "ai_summary_publish", "AISummary", s.pk, after={"edited": s.final_text != s.draft_text})
    return s


@transaction.atomic
def discard_summary(user, summary_id) -> AISummary:
    s = _summary_for(user, summary_id)
    s.reject(user)
    record(user, "ai_summary_reject", "AISummary", s.pk)
    return s


def summaries_for(user, f: Filters):
    """Published summaries for exactly these filters (newest first), and this person's open draft, if any."""
    base = AISummary.objects.filter(report__filters=f.as_dict()).select_related("reviewed_by", "report__generated_by")
    published_ = list(base.filter(status=SummaryStatus.ACCEPTED).order_by("-reviewed_at")[:3])
    draft = base.filter(status=SummaryStatus.DRAFT, report__generated_by=user).order_by("-generated_at").first()
    return published_, draft


def edit_distance_share(s: AISummary) -> float:
    """How much of the AI draft people changed (0 = published as written). Used in Phase 7 AI evaluation."""
    import difflib
    return round(1 - difflib.SequenceMatcher(None, s.draft_text, s.final_text).ratio(), 3)
