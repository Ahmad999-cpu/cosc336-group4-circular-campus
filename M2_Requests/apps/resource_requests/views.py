"""Screens of the Requests & Reservations module: new request, My requests, request panel, edit, cancel."""
import uuid

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.access.decorators import needs
from apps.catalogue.services import published
from apps.common.errors import ValidationFailed
from apps.web.htmx import is_htmx, with_toast

from . import services
from .forms import CancelForm, RequestForm
from .models import ResourceRequest
from .signals import request_sent

def _initial(request, asset):
    u = request.user
    units = services.request_units(u)
    dept = u.department if u.department and units.filter(pk=u.department.pk).exists() else units.first()
    return {
        "department": dept, "quantity": request.GET.get("qty") or 1, "purpose": request.GET.get("q", "")[:500],
        "destination_campus": (dept.campus if dept else "") or "Main", "destination_building": dept.building if dept else "",
        "idempotency_key": uuid.uuid4().hex,
    }


@needs("request.submit")
def new(request):
    """UC-23 (C4). From an item (Browse or Find: ?asset=<id>) or from scratch with a category."""
    asset = None
    asset_id = request.GET.get("asset") or request.POST.get("asset")
    if asset_id:
        try:
            asset = published().select_related("category", "owner_department").get(pk=asset_id)
        except Exception:  # unknown, unpublished or malformed id
            messages.error(request, _("That item is no longer offered for reuse. Pick another one."))
            return redirect("catalogue:browse")
    units = services.request_units(request.user)
    form = RequestForm(request.POST or None, units=units, asset=asset, initial=_initial(request, asset))
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        key = data.pop("idempotency_key")
        data["selected_asset"] = asset
        try:
            req, created = services.submit_request(request.user, data, key)
        except ValidationFailed as e:
            form.add_error(None, str(e))
        else:
            if created:
                request_sent.send(sender=ResourceRequest, request=req, by=request.user, match_ref=request.POST.get("match", ""))
            text = _("Request sent. You'll get a message when it's decided.") if created else _("Already sent. Here it is.")
            if is_htmx(request):
                resp = render(request, "resource_requests/_sent.html", {"req": req})
                return with_toast(resp, text, href=reverse("resource_requests:mine"), label=_("View"))
            messages.success(request, text)
            return redirect(reverse("resource_requests:mine") + f"#r-{req.pk}")
    ctx = {"form": form, "asset": asset, "match": request.GET.get("match") or request.POST.get("match", ""), "buy_new": (asset.estimated_value or 0) * int(form["quantity"].value() or 1) if asset and asset.estimated_value else None}
    template = "resource_requests/_new_drawer.html" if is_htmx(request) else "resource_requests/new.html"
    return render(request, template, ctx)


@needs("request.submit")
def mine(request):
    """UC-24 (C4): the person's own requests, with where each one is now."""
    which = request.GET.get("show", "open")
    if which not in ("open", "closed", "all"):
        which = "open"
    reqs = list(services.my_requests(request.user, which))
    for r in reqs:
        r.progress = services.progress_index(r)
    return render(request, "resource_requests/mine.html", {"requests": reqs, "which": which,
                                                           "open_n": services.my_requests(request.user, "open").count()})


def _mine_or_404(request, pk):
    req = get_object_or_404(ResourceRequest.objects.select_related("selected_asset", "category", "department", "requester"), pk=pk)
    if req.requester_id != request.user.pk:
        raise Http404()
    return req


@needs("request.submit")
def detail(request, pk):
    req = _mine_or_404(request, pk)
    req.progress = services.progress_index(req)
    events = []
    events.append({"what": _("Sent for approval"), "who": req.requester.full_name, "at": req.submitted_at})
    decision = getattr(req, "decision", None)
    if decision is not None:
        events.append({"what": (_("Approved") if decision.is_approval() else _("Rejected")) + (f": {decision.reason}" if decision.reason else ""),
                       "who": decision.reviewer.full_name, "at": decision.decided_at})
    for t in req.transfers.all():
        if t.dispatched_at:
            events.append({"what": _("Dispatched") + (f": {t.arrangements}" if t.arrangements else ""), "who": t.dispatched_by.full_name if t.dispatched_by else "", "at": t.dispatched_at})
        if t.received_at:
            events.append({"what": _("Received"), "who": t.received_by.full_name if t.received_by else "", "at": t.received_at})
    if req.status == "CANCELLED":
        events.append({"what": _("Cancelled: %(r)s") % {"r": req.cancel_reason}, "who": req.requester.full_name, "at": req.updated_at})
    events.sort(key=lambda e: e["at"], reverse=True)
    return render(request, "resource_requests/_detail.html", {"req": req, "events": events})


@needs("request.submit")
def edit(request, pk):
    req = _mine_or_404(request, pk)
    if not req.is_editable():
        raise Http404()
    initial = {f: getattr(req, f) for f in ("category", "quantity", "purpose", "specifications", "preferred_condition", "urgency",
                                          "required_date", "destination_campus", "destination_building", "destination_room")}
    form = RequestForm(request.POST or None, units=services.request_units(request.user), asset=req.selected_asset, editing=True, initial=initial)
    if request.method == "POST" and form.is_valid():
        changes = {k: v for k, v in form.cleaned_data.items() if getattr(req, k if k != "category" else "category") != v}
        try:
            services.edit_request(request.user, req, changes)
        except ValidationFailed as e:
            form.add_error(None, str(e))
        else:
            return redirect_mine(request, _("Request updated."))
    return render(request, "resource_requests/_edit_drawer.html", {"form": form, "req": req})


@needs("request.submit")
@require_POST
def cancel(request, pk):
    req = _mine_or_404(request, pk)
    form = CancelForm(request.POST)
    if not form.is_valid():
        raise ValidationFailed(_("Add a reason first."))
    services.cancel_request(request.user, req, form.cleaned_data["reason"])
    return redirect_mine(request, _("Request cancelled."))


def redirect_mine(request, text):
    """Back to My requests with a toast (a full reload, so every badge and step is current)."""
    from apps.web.htmx import redirect_htmx
    messages.success(request, text)
    url = reverse("resource_requests:mine")
    return redirect_htmx(url) if is_htmx(request) else redirect(url)
