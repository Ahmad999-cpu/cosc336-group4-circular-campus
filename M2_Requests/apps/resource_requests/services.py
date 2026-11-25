"""Public interface of the Requests & Reservations module (features 4.5 and 4.6; lab C4).

A request is created Pending approval. Reservations are created only by the approval transaction in the
Approvals & Transfers module (BR-6), so this module never touches asset quantities.
"""
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _l
from django.utils.translation import gettext as _t

from apps.access.models import Department, User
from apps.access.permissions import require, units_for, users_who_can
from apps.audit.services import record
from apps.catalogue.models import Asset, PublicationStatus
from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import NotificationType
from apps.notifications.services import Msg, enqueue

from .models import RequestStatus, ResourceRequest

OPEN = [RequestStatus.PENDING_APPROVAL, RequestStatus.APPROVED]
CLOSED = [RequestStatus.FULFILLED, RequestStatus.REJECTED, RequestStatus.CANCELLED]


def request_units(user: User):
    """Units this person may request for (their scope of request.submit)."""
    return units_for(user, "request.submit")


@transaction.atomic
def submit_request(by: User, data: dict, idempotency_key: str) -> tuple[ResourceRequest, bool]:
    """UC-23 (C4). Returns (request, created). The same idempotency key returns the first request (Table 9.1
    DUPLICATE), so a double click or a resent form never creates two."""
    existing = ResourceRequest.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.requester_id != by.pk:
            raise Forbidden("That form belongs to someone else")
        return existing, False
    dept: Department = data["department"]
    require(by, "request.submit", dept)
    asset: Asset | None = data.get("selected_asset")
    category = data.get("category")
    if asset is not None:
        if asset.publication_status != PublicationStatus.PUBLISHED:
            raise ValidationFailed("That item is no longer offered for reuse")
        if data["quantity"] > asset.unreserved_quantity:
            message = _t("Only %(n)s unit(s) of %(name)s are free") % {"n": asset.unreserved_quantity, "name": asset.name}
            raise ValidationFailed(message)
        if asset.owner_department_id == dept.pk:
            raise ValidationFailed("This item already belongs to that unit")
        category = asset.category
    if category is None:
        raise ValidationFailed("Choose a category")
    req = ResourceRequest(
        requester=by, department=dept, category=category, selected_asset=asset, purpose=data["purpose"].strip(),
        specifications=data.get("specifications", ""), quantity=data["quantity"],
        preferred_condition=data.get("preferred_condition") or "ANY", urgency=data.get("urgency") or "MEDIUM",
        destination_campus=data["destination_campus"], destination_building=data.get("destination_building", ""),
        destination_room=data.get("destination_room", ""), required_date=data.get("required_date"),
        idempotency_key=idempotency_key,
    )
    try:
        with transaction.atomic():
            req.submit()
    except IntegrityError:  # two submits raced on the same key
        return ResourceRequest.objects.get(idempotency_key=idempotency_key), False
    record(by, "submit_request", "ResourceRequest", req.pk,
           after={"qty": req.quantity, "asset": str(asset.pk) if asset else None, "department": str(dept)})
    what = f"{req.quantity} × {asset.name}" if asset else f"{req.quantity} × {category.name}"
    enqueue(by, NotificationType.REQUEST_SUBMITTED, Msg(_l("Your request for %(what)s was sent for approval."), what=what),
            f"ResourceRequest:{req.pk}", email=True)
    if asset is not None:
        for approver in users_who_can("request.approve", asset.owner_department):
            if approver.pk != by.pk:
                enqueue(approver, NotificationType.REQUEST_SUBMITTED,
                        Msg(_l("%(who)s (%(unit)s) asks for %(what)s."), who=by.full_name, unit=dept, what=what), f"ResourceRequest:{req.pk}")
    return req, True


def _own(by: User, req: ResourceRequest) -> None:
    if req.requester_id != by.pk:
        raise Forbidden("Only the person who made the request can change it")


@transaction.atomic
def edit_request(by: User, req: ResourceRequest, changes: dict) -> ResourceRequest:
    """UC-25: only while pending with no reservation (the model refuses otherwise)."""
    req = ResourceRequest.objects.select_for_update().get(pk=req.pk)
    _own(by, req)
    if "quantity" in changes and req.selected_asset_id and changes["quantity"] > req.selected_asset.unreserved_quantity:
        message = _t("Only %(n)s unit(s) are free") % {"n": req.selected_asset.unreserved_quantity}
        raise ValidationFailed(message)
    before = {k: str(getattr(req, k)) for k in changes}
    req.edit(changes)
    record(by, "edit_request", "ResourceRequest", req.pk, before=before, after={k: str(v) for k, v in changes.items()})
    return req


@transaction.atomic
def cancel_request(by: User, req: ResourceRequest, reason: str) -> ResourceRequest:
    """UC-50: a pending request. After approval the reservation is cancelled through the Approvals & Transfers
    module, which also releases the units exactly once."""
    req = ResourceRequest.objects.select_for_update().get(pk=req.pk)
    _own(by, req)
    if req.status != RequestStatus.PENDING_APPROVAL:
        raise ValidationFailed("Only pending requests can be cancelled here")
    req.cancel(reason)
    record(by, "cancel_request", "ResourceRequest", req.pk, after={"reason": reason})
    return req


def my_requests(user: User, which: str = "open"):
    qs = ResourceRequest.objects.filter(requester=user)
    if which == "open":
        qs = qs.filter(status__in=OPEN)
    elif which == "closed":
        qs = qs.filter(status__in=CLOSED)
    return qs.select_related("selected_asset", "category", "department").order_by("-submitted_at")


def attention_count(user: User) -> int:
    """Badge in the menu: approved requests whose items are on their way to this person's units."""
    from apps.access.permissions import units_for as _units
    units = _units(user, "transfer.receive")
    return ResourceRequest.objects.filter(Q(requester=user) | Q(department__in=units), status=RequestStatus.APPROVED,
                                          transfers__status="IN_TRANSIT").distinct().count()


def progress_index(req: ResourceRequest) -> int:
    """0 sent, 1 approved, 2 on its way, 3 received; -1 closed without delivery."""
    if req.status == RequestStatus.PENDING_APPROVAL:
        return 0
    if req.status == RequestStatus.FULFILLED:
        return 3
    if req.status == RequestStatus.APPROVED:
        t = req.transfers.order_by("-dispatched_at").first()
        return 2 if t is not None and t.dispatched_at else 1
    return -1
