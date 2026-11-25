"""Screens of the Life Cycle & Maintenance module: full history, maintenance board, end of life."""
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.permissions import can, has_any
from apps.catalogue import services as catalogue_services
from apps.catalogue.models import Asset
from apps.web.htmx import redirect_htmx, with_toast

from . import services
from .forms import EolForm, ProblemForm, RepairForm, ReturnForm
from .models import EndOfLifeProposal, EolStatus, LifeCycleEvent, MaintenanceRecord, MaintenanceStatus


@login_required
def history(request, pk):
    """C6: every event for one asset, who did it and when, plus the moves allowed from here."""
    asset = get_object_or_404(Asset.objects.select_related("category", "owner_department"), pk=pk)
    if not catalogue_services.can_view(request.user, asset):
        raise Http404()
    return render(request, "lifecycle/history.html", {
        "asset": asset, "events": services.history(asset), "next_states": services.next_states(asset),
        "can_correct": can(request.user, "asset.register", asset.owner_department),
        "can_maintain": can(request.user, "maintenance.record", asset.owner_department),
        "can_eol": can(request.user, "eol.propose", asset.owner_department),
    })


@login_required
@require_POST
def correct(request, event_pk):
    ev = get_object_or_404(LifeCycleEvent, pk=event_pk)
    services.correct_event(request.user, ev, request.POST.get("reason", ""))
    return redirect_htmx(reverse("lifecycle:history", args=[ev.asset_id]))


@login_required
def report(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if not can(request.user, "maintenance.record", asset.owner_department):
        raise Http404()
    form = ProblemForm(request.POST or None, initial={"condition": asset.condition})
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        services.report_problem(request.user, asset, description=d["description"], severity=d["severity"], condition=d["condition"],
                                inspection=d["kind"] == "inspection", urgency=d["urgency"], preferred_date=d["preferred_date"])
        return with_toast(render(request, "lifecycle/_done.html", {"asset": asset, "text": _("Recorded. Maintenance staff have been told.")}),
                          _("Problem recorded for %(name)s.") % {"name": asset.name})
    return render(request, "lifecycle/_report.html", {"asset": asset, "form": form})


SEVERITY_RANK = Case(When(severity="CRITICAL", then=Value(0)), When(severity="HIGH", then=Value(1)),
                     When(severity="MEDIUM", then=Value(2)), default=Value(3), output_field=IntegerField())


def _board_ctx(request, tab):
    recs = services.maintenance_for(request.user)
    return {
        "tab": tab,
        "open": recs.filter(status__in=services.OPEN_MAINTENANCE).annotate(rank=SEVERITY_RANK).order_by("rank", "opened_at"),
        "closed": recs.filter(status=MaintenanceStatus.CLOSED).order_by("-opened_at")[:6],
        "proposals": services.proposals_for(request.user).exclude(status=EolStatus.REJECTED).order_by("-proposed_at")[:50],
        "repair_form": RepairForm(), "return_form": ReturnForm(),
        "can_eol_approve": has_any(request.user, "eol.approve"),
    }


@login_required
def board(request):
    """Maintenance and end-of-life work, for maintenance staff, custodians and end-of-life reviewers."""
    if not (has_any(request.user, "maintenance.record") or has_any(request.user, "eol.approve")):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied()
    tab = request.GET.get("tab", "maintenance")
    return render(request, "lifecycle/board.html", _board_ctx(request, tab if tab in ("maintenance", "eol") else "maintenance"))


def _board_reply(request, text, tab="maintenance"):
    return with_toast(render(request, "lifecycle/_board_body.html", _board_ctx(request, tab)), text)


@needs("maintenance.record")
@require_POST
def start(request, rec_pk):
    rec = get_object_or_404(services.maintenance_for(request.user), pk=rec_pk)
    services.start_work(request.user, rec, request.POST.get("notes", ""))
    return _board_reply(request, _("Work started on %(name)s. It's out of the marketplace until it's back in service.") % {"name": rec.asset.name})


@needs("maintenance.record")
@require_POST
def repair(request, rec_pk):
    rec = get_object_or_404(services.maintenance_for(request.user), pk=rec_pk)
    form = RepairForm(request.POST)
    if not form.is_valid():
        from apps.common.errors import ValidationFailed
        raise ValidationFailed(_("Fill in what was repaired and the cost."))
    d = form.cleaned_data
    r = services.record_repair(request.user, rec, description=d["description"], actions=d["actions"], outcome=d["outcome"], cost=d["cost"])
    msg = _("Repair recorded. The custodian returns it to service.") if r.is_successful() else _("Recorded as unsuccessful. Start work again when ready.")
    return _board_reply(request, msg)


@needs("asset.custody")
@require_POST
def back_in_service(request, rec_pk):
    rec = get_object_or_404(MaintenanceRecord, pk=rec_pk)
    services.return_to_service(request.user, rec, request.POST.get("condition") or rec.current_condition)
    return _board_reply(request, _("%(name)s is available again. Publish it from Our assets if others can reuse it.") % {"name": rec.asset.name})


@login_required
def propose(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if not can(request.user, "eol.propose", asset.owner_department):
        raise Http404()
    # Feature 2: "Propose this" from the sustainable-action advice pre-selects the action; the person still chooses.
    form = EolForm(request.POST or None, initial={"action": request.GET.get("action")} if request.GET.get("action") else None)
    if request.method == "POST" and form.is_valid():
        services.propose_end_of_life(request.user, asset, form.cleaned_data["action"], form.cleaned_data["reason"])
        return with_toast(render(request, "lifecycle/_done.html", {"asset": asset, "text": _("Sent for an independent review. You'll be told the decision.")}),
                          _("Proposal sent."))
    return render(request, "lifecycle/_propose.html", {"asset": asset, "form": form})


@needs("eol.approve")
@require_POST
def decide(request, p_pk):
    p = get_object_or_404(EndOfLifeProposal, pk=p_pk)
    approve = request.POST.get("decision") == "approve"
    services.decide_end_of_life(request.user, p, approve, request.POST.get("reason", "").strip())
    return _board_reply(request, _("Approved. The custodian records it when it's done.") if approve else _("Rejected. The proposer has been told why."), "eol")


@needs("asset.custody")
@require_POST
def complete(request, p_pk):
    p = get_object_or_404(EndOfLifeProposal, pk=p_pk)
    asset = services.complete_end_of_life(request.user, p)
    return _board_reply(request, _("%(name)s is now %(state)s. Its history stays.") % {"name": asset.name, "state": asset.get_lifecycle_state_display().lower()}, "eol")


