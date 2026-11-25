"""Guest site: messages sent from the public contact form."""
from django.db import models

from apps.common.models import UUIDModel


class DeliveryStatus(models.TextChoices):
    SENT = "SENT", "Sent by e-mail"
    NOT_CONFIGURED = "NOT_CONFIGURED", "Saved; e-mail delivery not configured"
    FAILED = "FAILED", "Saved; e-mail sending failed"


class ContactMessage(UUIDModel):
    """Every message is stored first, so nothing is lost if e-mail is down or not set up yet.
    Staff can read them in the developer admin site."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    organisation = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField(max_length=4000)
    language = models.CharField(max_length=8, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)   # salted hash, for rate limiting only
    delivery = models.CharField(max_length=16, choices=DeliveryStatus.choices)
    delivery_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.organisation})"
