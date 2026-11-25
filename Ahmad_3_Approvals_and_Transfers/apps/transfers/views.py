"""Screens of the Approvals & Transfers module: approval queue, transfers board, receive, cancel."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.access.permissions import can
from apps.common.errors import ValidationFailed
from apps.resource_requests.models import ResourceRequest
from apps.web.htmx import is_htmx, redirect_htmx, with_toast

from . import services
from .models import DeliveryEventType, TransferStatus


def _queue_ctx(request):
    rows = []
    for req in services.queue_for(request.user):
        problem = services.approval_problem(request.user, req)
        rivals = list(services.competing(req))
        # Only a real competition: together they want more than is free.
        if rivals and req.selected_asset.unreserved_quantity >= req.quantity + sum(o.quantity for o in rivals):
            rivals = []
        rows.append({"req": req, "problem": problem, "rivals": rivals, "value": (req.selected_asset.estimated_value or 0) * req.quantity})
    oldest = rows[0]["req"].submitted_at if rows else None
    return {"rows": rows, "pending": sum(1 for r in rows if r["req"].requester_id != request.user.pk),
            "today": services.decided_today(request.user), "oldest": oldest}


@needs("request.approve")
def queue(request):
    """UC-32 to UC-34 (C5): requests for items the approver's units own, with every rule shown before clicking."""
    template = "transfers/_queue_body.html" if is_htmx(request) and request.GET.get("partial") else "transfers/queue.html"
    return render(request, template, _queue_ctx(request))


@needs("request.approve")
@require_POST
def approve(request, pk):
    req = get_object_or_404(ResourceRequest, pk=pk)
    version = request.POST.get("v")
    services.approve_request(req.pk, request.user, expected_row_version=int(version) if version else None)
    resp = render(request, "transfers/_queue_body.html", _queue_ctx(request))
    return with_toast(resp, _("Approved. %(n)s × %(name)s reserved for %(unit)s.") % {
        "n": req.quantity, "name": req.selected_asset.name, "unit": req.department.name})


@needs("request.approve")
@require_POST
def reject(request, pk):
    req = get_object_or_404(ResourceRequest, pk=pk)
    services.reject_request(req.pk, request.user, request.POST.get("reason", ""))
    resp = render(request, "transfers/_queue_body.html", _queue_ctx(request))
    return with_toast(resp, _("Rejected. %(name)s has been told why.") % {"name": req.requester.full_name})


def _board_ctx(request):
    qs = services.board_for(request.user)
    return {
        "awaiting": qs.filter(status=TransferStatus.AWAITING_DISPATCH, reservation__status="ACTIVE").order_by("request__required_date", "pk"),
        "transit": qs.filter(status=TransferStatus.IN_TRANSIT).prefetch_related("events").order_by("dispatched_at"),
        "done": qs.filter(status=TransferStatus.COMPLETED).order_by("-received_at")[:8],
        "arrangements": [_("Facilities van"), _("Trolley, same building"), _("Requester collects")],
        "event_types": [(DeliveryEventType.ATTEMPT_FAILED, _("Delivery attempt failed")), (DeliveryEventType.DISCREPANCY, _("Discrepancy")), (DeliveryEventType.NOTE, _("Note"))],
    }


@needs("transfer.dispatch")
def board(request):
    """UC-35 to UC-38: what to move, what is on its way, what arrived."""
    template = "transfers/_board_body.html" if is_htmx(request) and request.GET.get("partial") else "transfers/board.html"
    return render(request, template, _board_ctx(request))


@needs("transfer.dispatch")
@require_POST
def do_dispatch(request, pk):
    t = get_object_or_404(services.board_for(request.user), pk=pk)
    how = request.POST.get("how", "")
    note = request.POST.get("note", "").strip()
    services.dispatch(t.pk, request.user, f"{how}. {note}".strip(" .") if note else how)
    return with_toast(render(request, "transfers/_board_body.html", _board_ctx(request)),
                      _("%(name)s is on its way. The receiver confirms when it arrives.") % {"name": t.asset.name})


@needs("transfer.dispatch")
@require_POST
def delivery_event(request, pk):
    t = get_object_or_404(services.board_for(request.user), pk=pk)
    services.record_delivery_event(t.pk, request.user, request.POST.get("type", ""), request.POST.get("reason", ""))
    return with_toast(render(request, "transfers/_board_body.html", _board_ctx(request)), _("Recorded. The transfer stays in transit."))


@needs("transfer.dispatch")
@require_POST
def resolve(request, event_pk):
    services.resolve_event(event_pk, request.user)
    return with_toast(render(request, "transfers/_board_body.html", _board_ctx(request)), _("Marked as resolved."))


@needs("transfer.receive")
def receive(request, pk):
    """UC-37: the receiver confirms what arrived (side panel opened from My requests)."""
    req = get_object_or_404(ResourceRequest.objects.select_related("selected_asset", "department"), pk=pk)
    t = services.transfer_for_request(req)
    if t is None or not can(request.user, "transfer.receive", t.destination_department):
        raise Http404()
    error = ""
    if request.method == "POST":
        try:
            qty = int(request.POST.get("quantity", "0"))
        except ValueError:
            qty = 0
        if qty == t.quantity:
            moved = services.confirm_receipt(t.pk, request.user, qty, replaced_planned_purchase=bool(request.POST.get("replaced")))
            messages.success(request, _("Receipt confirmed. %(name)s now belongs to %(unit)s.") % {"name": moved.name, "unit": moved.owner_department.name},
                             extra_tags="celebrate")
            return redirect_htmx(reverse("resource_requests:mine")) if is_htmx(request) else redirect("resource_requests:mine")
        if 0 <= qty < t.quantity:
            services.record_delivery_event(t.pk, request.user, DeliveryEventType.DISCREPANCY,
                                           _("Received %(got)s of %(sent)s") % {"got": qty, "sent": t.quantity}, request.POST.get("note", ""))
            messages.info(request, _("Recorded a discrepancy. Facilities will follow up; nothing has moved yet."))
            return redirect_htmx(reverse("resource_requests:mine")) if is_htmx(request) else redirect("resource_requests:mine")
        error = _("Enter a number between 0 and %(n)s.") % {"n": t.quantity}
    return render(request, "transfers/_receive.html", {"req": req, "t": t, "error": error})


@needs("request.submit")
@require_POST
def cancel(request, pk):
    """UC-30 from My requests: cancel an approved request before it is dispatched."""
    req = get_object_or_404(ResourceRequest, pk=pk)
    reason = request.POST.get("reason", "").strip()
    if not reason:
        raise ValidationFailed(_("Add a reason first."))
    services.cancel_reservation(req.pk, request.user, reason)
    messages.success(request, _("Request cancelled. The units are free again."))
    url = reverse("resource_requests:mine")
    return redirect_htmx(url) if is_htmx(request) else redirect(url)



