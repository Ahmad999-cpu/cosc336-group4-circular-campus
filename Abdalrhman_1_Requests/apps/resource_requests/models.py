"""Requests & Reservations module (features 4.5 requests, 4.6 reservations; assistant drafts from 4.15).

Classes: ResourceRequest, Reservation, ReservationEvent, AssistantDraft.
State machines: request (Figure 7.6) and reservation (Figure 7.7).
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import Department, User
from apps.catalogue.models import Asset, Category
from apps.common.enums import PreferredCondition, Urgency
from apps.common.errors import ValidationFailed
from apps.common.models import Location, UUIDModel
from apps.common.statemachine import move


class RequestStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")
    FULFILLED = "FULFILLED", _("Fulfilled")


REQUEST_TRANSITIONS = {
    RequestStatus.PENDING_APPROVAL: {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED},
    RequestStatus.APPROVED: {RequestStatus.FULFILLED, RequestStatus.CANCELLED},
    RequestStatus.REJECTED: set(),
    RequestStatus.CANCELLED: set(),
    RequestStatus.FULFILLED: set(),
}


class ResourceRequest(UUIDModel):
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name="requests")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="requests")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="requests")
    selected_asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.PROTECT, related_name="selected_in")

    purpose = models.TextField()
    specifications = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    preferred_condition = models.CharField(max_length=10, choices=PreferredCondition.choices, default=PreferredCondition.ANY)
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.MEDIUM)
    destination_campus = models.CharField(max_length=100)
    destination_building = models.CharField(max_length=100, blank=True)
    destination_room = models.CharField(max_length=50, blank=True)
    required_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING_APPROVAL, editable=False)
    cancel_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    idempotency_key = models.CharField(max_length=64, unique=True, help_text=_("Stops a double-click creating two requests"))
    row_version = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.quantity} × {self.category.name} for {self.department}"

    @property
    def destination(self) -> Location:
        return Location(self.destination_campus, self.destination_building, self.destination_room)

    def _save(self, *fields: str) -> None:
        self.row_version += 1
        self.save(update_fields=[*fields, "row_version", "updated_at"])

    # --- class diagram operations ---
    def submit(self) -> None:
        """Validate BR-4 and save as Pending Approval. Use the Requests service, which also checks permission."""
        if self.quantity < 1:
            raise ValidationFailed("Quantity must be at least 1")
        if not self.purpose.strip():
            raise ValidationFailed("Purpose is required")
        if self.required_date and self.required_date < timezone.localdate():
            raise ValidationFailed("Required date is in the past")
        self.status = RequestStatus.PENDING_APPROVAL
        self.save()

    def is_editable(self) -> bool:
        """Edit only while pending and with no reservation (UC-25)."""
        return self.status == RequestStatus.PENDING_APPROVAL and not hasattr(self, "reservation")

    EDITABLE_FIELDS = ("purpose", "specifications", "quantity", "preferred_condition", "urgency", "destination_campus",
                       "destination_building", "destination_room", "required_date", "category")

    def edit(self, form: dict) -> None:
        if not self.is_editable():
            raise ValidationFailed("This request can no longer be edited")
        bad = set(form) - set(self.EDITABLE_FIELDS)
        if bad:
            raise ValidationFailed(f"Fields not editable: {', '.join(sorted(bad))}")
        for k, v in form.items():
            setattr(self, k, v)
        self._save(*form.keys())

    def select_asset(self, asset_id) -> None:
        if self.status != RequestStatus.PENDING_APPROVAL:
            raise ValidationFailed("Only pending requests can change the selected asset")
        self.selected_asset_id = asset_id
        self._save("selected_asset")

    def cancel(self, reason: str) -> None:
        if not reason.strip():
            raise ValidationFailed("A reason is required to cancel")
        move(self, "status", RequestStatus.CANCELLED, REQUEST_TRANSITIONS)
        self.cancel_reason = reason
        self._save("status", "cancel_reason")

    def approve(self) -> None:
        """State change only. The approval transaction (transfers.services.approve_request) does the checks."""
        move(self, "status", RequestStatus.APPROVED, REQUEST_TRANSITIONS)
        self._save("status")

    def reject(self, reason: str) -> None:
        if not reason.strip():
            raise ValidationFailed("A reason is required to reject")
        move(self, "status", RequestStatus.REJECTED, REQUEST_TRANSITIONS)
        self._save("status")

    def fulfil(self) -> None:
        move(self, "status", RequestStatus.FULFILLED, REQUEST_TRANSITIONS)
        self._save("status")


class ReservationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    CANCELLED = "CANCELLED", _("Cancelled")
    FULFILLED = "FULFILLED", _("Fulfilled")


RESERVATION_TRANSITIONS = {
    ReservationStatus.ACTIVE: {ReservationStatus.CANCELLED, ReservationStatus.FULFILLED},
    ReservationStatus.CANCELLED: set(),
    ReservationStatus.FULFILLED: set(),
}


class Reservation(UUIDModel):
    """Created only inside the approval transaction (BR-6)."""

    request = models.OneToOneField(ResourceRequest, on_delete=models.PROTECT, related_name="reservation")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="reservations")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=ReservationStatus.choices, default=ReservationStatus.ACTIVE, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cancel_reason = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def is_active(self) -> bool:
        return self.status == ReservationStatus.ACTIVE

    def _log(self, action: str, by: User, reason: str = "") -> None:
        ReservationEvent.objects.create(reservation=self, actor=by, action=action, reason=reason)

    def cancel(self, reason: str, by: User) -> None:
        """Cancel before dispatch (UC-30). The caller must also release the units once via Asset.release."""
        transfer = getattr(self, "transfer", None)
        if transfer is not None and transfer.dispatched_at is not None:
            raise ValidationFailed("Already dispatched; record a delivery event instead")
        if not reason.strip():
            raise ValidationFailed("A reason is required")
        move(self, "status", ReservationStatus.CANCELLED, RESERVATION_TRANSITIONS)
        self.cancel_reason, self.closed_at = reason, timezone.now()
        self.save(update_fields=["status", "cancel_reason", "closed_at"])
        self._log("CANCELLED", by, reason)

    def fulfil(self, by: User) -> None:
        move(self, "status", ReservationStatus.FULFILLED, RESERVATION_TRANSITIONS)
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at"])
        self._log("FULFILLED", by)


class ReservationEvent(UUIDModel):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["occurred_at"]


class DraftStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    DISCARDED = "DISCARDED", _("Discarded")


class AssistantDraft(UUIDModel):
    """A request the assistant prepared. It becomes a ResourceRequest only when the user confirms (FR-14.9)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assistant_drafts")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="+")
    draft_fields = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=DraftStatus.choices, default=DraftStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    resulting_request = models.OneToOneField(ResourceRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="assistant_draft")

    def is_confirmed(self) -> bool:
        return self.status == DraftStatus.CONFIRMED

    def confirm(self, request: ResourceRequest) -> None:
        if self.status != DraftStatus.DRAFT:
            raise ValidationFailed("Draft already closed")
        self.status, self.confirmed_at, self.resulting_request = DraftStatus.CONFIRMED, timezone.now(), request
        self.save()

    def discard(self) -> None:
        self.status = DraftStatus.DISCARDED
        self.save(update_fields=["status"])
