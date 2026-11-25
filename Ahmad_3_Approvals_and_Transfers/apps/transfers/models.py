"""Approvals & Transfers module (features 4.7 approvals, 4.8 transfers).

Classes: ApprovalDecision, Transfer, DeliveryEvent. Transfer state machine: Figure 7.8.
The approval transaction lives in services.approve_request (it locks the asset row).
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import Department, User
from apps.catalogue.models import Asset
from apps.common.errors import ValidationFailed
from apps.common.models import Location, UUIDModel
from apps.common.statemachine import move
from apps.resource_requests.models import Reservation, ResourceRequest


class DecisionType(models.TextChoices):
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class ApprovalDecision(UUIDModel):
    request = models.OneToOneField(ResourceRequest, on_delete=models.PROTECT, related_name="decision")
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="decisions")
    decision = models.CharField(max_length=10, choices=DecisionType.choices)
    reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def is_approval(self) -> bool:
        return self.decision == DecisionType.APPROVED


class TransferStatus(models.TextChoices):
    AWAITING_DISPATCH = "AWAITING_DISPATCH", _("Awaiting dispatch")
    IN_TRANSIT = "IN_TRANSIT", _("In transit")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


TRANSFER_TRANSITIONS = {
    TransferStatus.AWAITING_DISPATCH: {TransferStatus.IN_TRANSIT, TransferStatus.CANCELLED},
    TransferStatus.IN_TRANSIT: {TransferStatus.COMPLETED},  # a failed delivery stays In Transit (FR-8.16)
    TransferStatus.COMPLETED: set(),
    TransferStatus.CANCELLED: set(),
}


class Transfer(UUIDModel):
    request = models.ForeignKey(ResourceRequest, on_delete=models.PROTECT, related_name="transfers")
    reservation = models.OneToOneField(Reservation, on_delete=models.PROTECT, related_name="transfer")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="transfers")
    source_department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="outgoing_transfers")
    destination_department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="incoming_transfers")
    source_campus = models.CharField(max_length=100)
    source_building = models.CharField(max_length=100, blank=True)
    source_room = models.CharField(max_length=50, blank=True)
    destination_campus = models.CharField(max_length=100)
    destination_building = models.CharField(max_length=100, blank=True)
    destination_room = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField()
    arrangements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TransferStatus.choices, default=TransferStatus.AWAITING_DISPATCH, editable=False)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    dispatched_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    received_quantity = models.PositiveIntegerField(null=True, blank=True)
    # Addition (pilot "verified savings"): the receiver confirms this transfer replaced a purchase they had planned.
    replaced_planned_purchase = models.BooleanField(default=False)

    @property
    def source_location(self) -> Location:
        return Location(self.source_campus, self.source_building, self.source_room)

    @property
    def destination_location(self) -> Location:
        return Location(self.destination_campus, self.destination_building, self.destination_room)

    # --- class diagram operations ---
    def dispatch(self, arrangements: str, by: User) -> None:
        if self.quantity != self.reservation.quantity:
            raise ValidationFailed("Dispatch quantity must equal the reserved quantity")
        move(self, "status", TransferStatus.IN_TRANSIT, TRANSFER_TRANSITIONS)
        self.arrangements, self.dispatched_at, self.dispatched_by = arrangements, timezone.now(), by
        self.save(update_fields=["status", "arrangements", "dispatched_at", "dispatched_by"])

    def record_attempt(self, e: "DeliveryEvent") -> None:
        if self.status != TransferStatus.IN_TRANSIT:
            raise ValidationFailed("Delivery events are recorded only while in transit")
        e.transfer = self
        e.save()

    def has_open_discrepancy(self) -> bool:
        return self.events.filter(event_type=DeliveryEventType.DISCREPANCY, resolved=False).exists()

    def complete(self, qty: int, by: User) -> None:
        """Receiver confirms. Use transfers.services.confirm_receipt, which also moves the units (BR-9)."""
        if qty != self.quantity:
            raise ValidationFailed("Received quantity differs; record a discrepancy instead")
        if self.has_open_discrepancy():
            raise ValidationFailed("Resolve the open discrepancy first")
        move(self, "status", TransferStatus.COMPLETED, TRANSFER_TRANSITIONS)
        self.received_at, self.received_by, self.received_quantity = timezone.now(), by, qty
        self.save(update_fields=["status", "received_at", "received_by", "received_quantity"])

    def cancel(self) -> None:
        move(self, "status", TransferStatus.CANCELLED, TRANSFER_TRANSITIONS)
        self.save(update_fields=["status"])


class DeliveryEventType(models.TextChoices):
    ATTEMPT_FAILED = "ATTEMPT_FAILED", _("Delivery attempt failed")
    DISCREPANCY = "DISCREPANCY", _("Discrepancy")
    NOTE = "NOTE", _("Note")
    CORRECTION = "CORRECTION", _("Correction")


class DeliveryEvent(UUIDModel):
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=DeliveryEventType.choices)
    reason = models.TextField(blank=True)
    details = models.TextField(blank=True)
    event_time = models.DateTimeField(default=timezone.now)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    resolved = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    corrects = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="corrections")

    def correct(self, reason: str, by: User) -> "DeliveryEvent":
        """Events are never edited; a correction is a new event pointing at the old one."""
        return DeliveryEvent.objects.create(transfer=self.transfer, event_type=DeliveryEventType.CORRECTION,
                                            reason=reason, recorded_by=by, corrects=self)

    def resolve(self, by: User) -> None:
        self.resolved, self.verified_by = True, by
        self.save(update_fields=["resolved", "verified_by"])
