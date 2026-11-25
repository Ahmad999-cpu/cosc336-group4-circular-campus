"""Audit module (NFR-18): append-only log of security-sensitive actions and denied attempts."""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.common.errors import ValidationFailed
from apps.common.models import UUIDModel


class AuditOutcome(models.TextChoices):
    SUCCESS = "SUCCESS", _("Success")
    DENIED = "DENIED", _("Denied")
    FAILED = "FAILED", _("Failed")


class AuditLog(UUIDModel):
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=60, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    before_value = models.JSONField(null=True, blank=True)
    after_value = models.JSONField(null=True, blank=True)
    outcome = models.CharField(max_length=8, choices=AuditOutcome.choices, default=AuditOutcome.SUCCESS)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationFailed("AuditLog is append-only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationFailed("AuditLog is append-only")
