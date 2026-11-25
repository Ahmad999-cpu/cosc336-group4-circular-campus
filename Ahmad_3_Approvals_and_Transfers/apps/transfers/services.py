"""Public interface of the Approvals & Transfers module (features 4.7 and 4.8; lab C5).

C5: "at least one approval step, with no self-approval. The receiver confirms; owner and department change.
The last item cannot go to two people."
Every function that changes quantities locks the rows it changes (SELECT ... FOR UPDATE) inside one
transaction, so two people acting at the same moment are processed one after the other.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l
from django.utils.translation import gettext as _t

from apps.access.models import User
from apps.access.permissions import can, require, units_for, users_who_can
from apps.audit.services import record
from apps.blueprint.routing import approval_route
from apps.catalogue.models import Asset, PublicationStatus
from apps.common.errors import Conflict, DomainError, Forbidden, InsufficientQuantity, SelfApproval, ValidationFailed
from apps.notifications.models import NotificationType
from apps.notifications.services import Msg, enqueue
from apps.resource_requests.models import RequestStatus, Reservation, ReservationEvent, ResourceRequest

from .models import ApprovalDecision, DecisionType, DeliveryEvent, DeliveryEventType, Transfer, TransferStatus
from .signals import transfer_received


# ---------------------------------------------------------------- approval checks

def approval_problem(reviewer: User, req: ResourceRequest, asset: Asset | None = None) -> DomainError | None:
    """Every rule an approval must pass, in the order of Section 9.9. Returns the first problem, or None.
    Used by approve_request (which raises it) and by the queue (which shows it next to the button)."""
    if req.status != RequestStatus.PENDING_APPROVAL:
        return DomainError("This request has already been decided", code="NOT_PENDING")
    if reviewer.pk == req.requester_id:
        return SelfApproval("Your own request: another approver must decide (BR-5)")
    asset = asset or req.selected_asset
    if asset is None:
        return ValidationFailed("No item chosen yet: the requester picks one from the matches")
    value = asset.estimated_value * req.quantity if asset.estimated_value is not None else None
    if not can(reviewer, "request.approve", asset.owner_department):
        return Forbidden("Only approvers for the owning unit can decide")
    if not can(reviewer, "request.approve", asset.owner_department, value=value):
        return Forbidden("Above your approval limit: a higher approver decides")
    route = approval_route(asset, req.quantity)  # Institution Blueprint
    if route is not None:
        role, unit = route
        if not reviewer.has_role(role.name, unit):
            message = _t("The approval rules send this to: %(role)s") % {"role": role.display_name}
            return Forbidden(message)
    if asset.publication_status != PublicationStatus.PUBLISHED:
        return DomainError("The item is no longer published", code="INELIGIBLE")
    if asset.unreserved_quantity < req.quantity:
        message = _t("Only %(n)s unit(s) free now") % {"n": asset.unreserved_quantity}
        return InsufficientQuantity(message)
    return None


@transaction.atomic
def approve_request(request_id, reviewer: User, *, asset_id=None, expected_row_version: int | None = None) -> Reservation:
    """UC-33. One transaction: lock -> checks -> decision -> allocate units -> reservation -> transfer -> notify."""
    req = ResourceRequest.objects.select_for_update().get(pk=request_id)
    if expected_row_version is not None and req.row_version != expected_row_version:
        raise Conflict("The request changed since you opened it; reload and try again")
    asset_id = asset_id or req.selected_asset_id
    asset = Asset.objects.select_for_update().get(pk=asset_id) if asset_id else None
    problem = approval_problem(reviewer, req, asset)
    if problem is not None:
        if isinstance(problem, (SelfApproval, Forbidden)):
            record(reviewer, "approve_request", "ResourceRequest", req.pk, outcome="DENIED", after={"reason": problem.code})
        raise problem

    asset.allocate(req.quantity, reviewer)  # BR-7, re-checked on the locked row
    if req.selected_asset_id != asset.pk:
        req.select_asset(asset.pk)
    req.approve()
    ApprovalDecision.objects.create(request=req, reviewer=reviewer, decision=DecisionType.APPROVED)
    reservation = Reservation.objects.create(request=req, asset=asset, created_by=reviewer, quantity=req.quantity)
    ReservationEvent.objects.create(reservation=reservation, actor=reviewer, action="CREATED")
    Transfer.objects.create(
        request=req, reservation=reservation, asset=asset, quantity=req.quantity,
        source_department=asset.owner_department, destination_department=req.department,
        source_campus=asset.location_campus, source_building=asset.location_building, source_room=asset.location_room,
        destination_campus=req.destination_campus, destination_building=req.destination_building,
        destination_room=req.destination_room,
    )
    enqueue(req.requester, NotificationType.REQUEST_APPROVED,
            Msg(_l("Approved: %(n)s × %(name)s. Facilities will arrange the move."), n=req.quantity, name=asset.name),
            f"ResourceRequest:{req.pk}", email=True)
    for person in users_who_can("transfer.dispatch", asset.owner_department):
        enqueue(person, NotificationType.REQUEST_APPROVED,
                Msg(_l("To move: %(n)s × %(name)s to %(unit)s."), n=req.quantity, name=asset.name, unit=req.department),
                f"ResourceRequest:{req.pk}")
    record(reviewer, "approve_request", "ResourceRequest", req.pk, after={"asset": str(asset.pk), "qty": req.quantity})
    return reservation


@transaction.atomic
def reject_request(request_id, reviewer: User, reason: str) -> ResourceRequest:
    """UC-34. Same checks as approving (pending, not one's own, permission), then a reason for the requester."""
    req = ResourceRequest.objects.select_for_update(of=("self",)).select_related("selected_asset").get(pk=request_id)
    if not reason.strip():
        raise ValidationFailed("Tell the requester why")
    if req.status != RequestStatus.PENDING_APPROVAL:
        raise DomainError("This request has already been decided", code="NOT_PENDING")
    if reviewer.pk == req.requester_id:
        raise SelfApproval("Your own request: another approver must decide (BR-5)")
    # Rejecting needs the approver role for the owning unit, but not the value limit: an item that ran out,
    # was withdrawn or is above one's limit can still be turned down with a reason.
    dept = req.selected_asset.owner_department if req.selected_asset_id else None
    if not can(reviewer, "request.approve", dept):
        raise Forbidden("Only approvers for the owning unit can decide")
    req.reject(reason)
    ApprovalDecision.objects.create(request=req, reviewer=reviewer, decision=DecisionType.REJECTED, reason=reason)
    what = req.selected_asset.name if req.selected_asset else req.category.name
    enqueue(req.requester, NotificationType.REQUEST_REJECTED,
            Msg(_l("Not approved: %(n)s × %(name)s. Reason: %(reason)s"), n=req.quantity, name=what, reason=reason),
            f"ResourceRequest:{req.pk}", email=True)
    record(reviewer, "reject_request", "ResourceRequest", req.pk, after={"reason": reason})
    return req


# ---------------------------------------------------------------- transfers

@transaction.atomic
def dispatch(transfer_id, by: User, arrangements: str) -> Transfer:
    """UC-35. Facilities records how and when the item leaves. Custody does NOT change here (BR-9)."""
    transfer = Transfer.objects.select_for_update().select_related("reservation", "request", "asset").get(pk=transfer_id)
    require(by, "transfer.dispatch", transfer.source_department)
    if not transfer.reservation.is_active():
        raise ValidationFailed("The reservation was cancelled")
    transfer.dispatch(arrangements.strip(), by)
    enqueue(transfer.request.requester, NotificationType.TRANSFER_DISPATCHED,
            Msg(_l("On its way: %(n)s × %(name)s (%(how)s). Confirm when it arrives."), n=transfer.quantity,
                name=transfer.asset.name, how=arrangements.strip() or _l("no notes")),
            f"ResourceRequest:{transfer.request_id}", email=True)
    record(by, "dispatch", "Transfer", transfer.pk, after={"arrangements": arrangements})
    return transfer


@transaction.atomic
def record_delivery_event(transfer_id, by: User, event_type: str, reason: str, details: str = "") -> DeliveryEvent:
    """UC-38. A failed attempt or a discrepancy keeps the transfer In transit; it never returns to stock by itself."""
    transfer = Transfer.objects.select_for_update().get(pk=transfer_id)
    if not (can(by, "transfer.dispatch", transfer.source_department) or can(by, "transfer.receive", transfer.destination_department)):
        raise Forbidden("Only Facilities or the receiving unit can record delivery events")
    if event_type not in (DeliveryEventType.ATTEMPT_FAILED, DeliveryEventType.DISCREPANCY, DeliveryEventType.NOTE):
        raise ValidationFailed("Unknown delivery event")
    if not reason.strip():
        raise ValidationFailed("Describe what happened")
    ev = DeliveryEvent(event_type=event_type, reason=reason.strip(), details=details, recorded_by=by)
    transfer.record_attempt(ev)
    if event_type == DeliveryEventType.DISCREPANCY and transfer.dispatched_by_id:
        enqueue(transfer.dispatched_by, NotificationType.OTHER,
                Msg(_l("Discrepancy on %(name)s: %(reason)s"), name=transfer.asset.name, reason=reason), f"Transfer:{transfer.pk}")
    record(by, "delivery_event", "Transfer", transfer.pk, after={"type": event_type, "reason": reason})
    return ev


@transaction.atomic
def resolve_event(event_id, by: User) -> DeliveryEvent:
    ev = DeliveryEvent.objects.select_related("transfer").get(pk=event_id)
    require(by, "transfer.dispatch", ev.transfer.source_department)
    ev.resolve(by)
    record(by, "resolve_delivery_event", "Transfer", ev.transfer_id, after={"event": str(ev.pk)})
    return ev


@transaction.atomic
def cancel_reservation(request_id, by: User, reason: str) -> ResourceRequest:
    """UC-30. Before dispatch only. Releases the reserved units exactly once, then closes the reservation,
    the transfer and the request. Allowed for the requester, or an approver for the owning unit."""
    req = ResourceRequest.objects.select_for_update().get(pk=request_id)
    reservation = Reservation.objects.select_for_update().get(request=req)
    asset = Asset.objects.select_for_update().get(pk=reservation.asset_id)
    if not (req.requester_id == by.pk or can(by, "request.approve", asset.owner_department)):
        raise Forbidden("Only the requester or an approver can cancel")
    if not reason.strip():
        raise ValidationFailed("A reason is required")
    reservation.cancel(reason, by)          # refuses after dispatch
    asset.release(reservation.quantity, by)  # once: the reservation can only be cancelled once
    transfer = getattr(reservation, "transfer", None)
    if transfer is not None:
        Transfer.objects.select_for_update().get(pk=transfer.pk).cancel()
    req.cancel(reason)
    if req.requester_id != by.pk:
        enqueue(req.requester, NotificationType.REQUEST_CANCELLED,
                Msg(_l("Cancelled: %(n)s × %(name)s. Reason: %(reason)s"), n=req.quantity, name=asset.name, reason=reason),
                f"ResourceRequest:{req.pk}")
    record(by, "cancel_reservation", "ResourceRequest", req.pk, after={"reason": reason, "released": reservation.quantity})
    return req


@transaction.atomic
def confirm_receipt(transfer_id, receiver: User, quantity: int, replaced_planned_purchase: bool = False) -> Asset:
    """UC-37. The receiver confirms; only now do owner, department, custodian and location change (BR-9).
    Returns the asset record that now holds the units (a new record if part of a lot moved)."""
    transfer = Transfer.objects.select_for_update().select_related("reservation", "request").get(pk=transfer_id)
    require(receiver, "transfer.receive", transfer.destination_department)
    asset = Asset.objects.select_for_update().get(pk=transfer.asset_id)

    transfer.complete(quantity, receiver)  # needs In transit, same quantity, no open discrepancy (BR-8)
    if replaced_planned_purchase:
        transfer.replaced_planned_purchase = True
        transfer.save(update_fields=["replaced_planned_purchase"])
    moved = asset.move_units(quantity, transfer.destination_location, transfer.destination_department,
                             custodian=receiver, by=receiver)
    transfer.reservation.fulfil(receiver)
    transfer.request.fulfil()
    for person in {p for p in [transfer.dispatched_by, asset.custodian] if p is not None and p.pk != receiver.pk}:
        enqueue(person, NotificationType.TRANSFER_RECEIVED,
                Msg(_l("%(unit)s confirmed receipt of %(n)s × %(name)s."), unit=transfer.request.department, n=quantity,
                    name=asset.name), f"Transfer:{transfer.pk}")
    record(receiver, "confirm_receipt", "Transfer", transfer.pk,
           after={"asset": str(moved.pk), "qty": quantity, "replaced_planned_purchase": replaced_planned_purchase})
    transfer_received.send(sender=Transfer, transfer=transfer, quantity=quantity, by=receiver)  # same transaction
    return moved


# ---------------------------------------------------------------- reading

def queue_for(user: User):
    """Pending requests for items owned by the units this person approves for (oldest first)."""
    units = units_for(user, "request.approve")
    return (ResourceRequest.objects.filter(status=RequestStatus.PENDING_APPROVAL, selected_asset__owner_department__in=units)
            .select_related("requester", "department", "selected_asset", "selected_asset__owner_department", "category")
            .order_by("submitted_at"))


def pending_count(user: User) -> int:
    return queue_for(user).exclude(requester=user).count()


def decided_today(user: User) -> int:
    since = timezone.now() - timedelta(hours=24)
    return ApprovalDecision.objects.filter(reviewer=user, decided_at__gte=since).count()


def board_for(user: User):
    units = units_for(user, "transfer.dispatch")
    return (Transfer.objects.filter(source_department__in=units)
            .select_related("asset", "request", "request__requester", "source_department", "destination_department", "dispatched_by"))


def to_dispatch_count(user: User) -> int:
    return board_for(user).filter(status=TransferStatus.AWAITING_DISPATCH, reservation__status="ACTIVE").count()


def transfer_for_request(req: ResourceRequest) -> Transfer | None:
    return req.transfers.exclude(status=TransferStatus.CANCELLED).order_by("-reservation__created_at").first()


def competing(req: ResourceRequest):
    """Other pending requests for the same item (BR-13: decision support for competing requests)."""
    if not req.selected_asset_id:
        return ResourceRequest.objects.none()
    return ResourceRequest.objects.filter(status=RequestStatus.PENDING_APPROVAL, selected_asset_id=req.selected_asset_id).exclude(pk=req.pk)
