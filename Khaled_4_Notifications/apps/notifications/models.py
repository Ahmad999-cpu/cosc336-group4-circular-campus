"""Notifications module (C8; ADR-4 outbox). Other modules call services.enqueue inside their transaction;
the worker delivers e-mail later, so a mail failure never rolls back a business record."""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.common.models import UUIDModel


class Channel(models.TextChoices):
    IN_APP = "IN_APP", _("In-app")
    EMAIL = "EMAIL", _("E-mail")


class NotificationType(models.TextChoices):
    REQUEST_SUBMITTED = "REQUEST_SUBMITTED", _("Request submitted")
    REQUEST_APPROVED = "REQUEST_APPROVED", _("Request approved")
    REQUEST_REJECTED = "REQUEST_REJECTED", _("Request rejected")
    REQUEST_CANCELLED = "REQUEST_CANCELLED", _("Request cancelled")
    TRANSFER_DISPATCHED = "TRANSFER_DISPATCHED", _("Transfer dispatched")
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED", _("Transfer received")
    ASSET_REGISTERED = "ASSET_REGISTERED", _("Asset registered")
    MAINTENANCE_UPDATE = "MAINTENANCE_UPDATE", _("Maintenance update")
    REPORT_READY = "REPORT_READY", _("Report summary ready")
    NEED_MATCH = "NEED_MATCH", _("Saved need matched")              # Phase 5
    AVAILABILITY = "AVAILABILITY", _("Availability date changed")  # Phase 6
    ASSET_QUESTION = "ASSET_QUESTION", _("Question about an asset")  # Phase 7
    ASSET_ANSWER = "ASSET_ANSWER", _("Answer to your question")      # Phase 7
    OTHER = "OTHER", _("Other")


class DeliveryStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    SENT = "SENT", _("Sent")
    FAILED = "FAILED", _("Failed")


class Notification(UUIDModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=8, choices=Channel.choices, default=Channel.IN_APP)
    event_type = models.CharField(max_length=24, choices=NotificationType.choices)
    subject_ref = models.CharField(max_length=80, blank=True, help_text=_("e.g. ResourceRequest:<uuid>"))
    message = models.TextField()
    message_ar = models.TextField(blank=True)  # design change 17: the same message in Arabic, written when sent
    delivery_status = models.CharField(max_length=8, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)  # addition: in-app unread badge

    class Meta:
        ordering = ["-created_at"]

    @property
    def text(self) -> str:
        """The message in the reader's interface language (Arabic when available)."""
        from django.utils.translation import get_language
        return self.message_ar if self.message_ar and (get_language() or "").startswith("ar") else self.message

    def mark_sent(self) -> None:
        self.delivery_status, self.sent_at = DeliveryStatus.SENT, timezone.now()
        self.save(update_fields=["delivery_status", "sent_at"])

    def mark_failed(self, reason: str) -> None:
        self.delivery_status, self.failure_reason = DeliveryStatus.FAILED, reason
        self.save(update_fields=["delivery_status", "failure_reason"])
