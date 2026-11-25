"""AI Gateway module data (store D13 model versions and inference log; D14 policy documents).

Classes: ModelVersion, AIInferenceRecord, PolicyDocument.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.common.enums import RecordStatus, UserDecision
from apps.common.models import UUIDModel


class AICapability(models.TextChoices):
    CLASSIFY = "CLASSIFY", _("Asset classification")
    EMBED = "EMBED", _("Semantic embeddings")
    RANK = "RANK", _("Match ranking")
    RECOMMEND = "RECOMMEND", _("Sustainable-action advice")
    CHAT = "CHAT", _("Assistant")
    SUMMARIZE = "SUMMARIZE", _("Report summary")
    BLUEPRINT = "BLUEPRINT", _("Blueprint drafting")


class ModelStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    DISABLED = "DISABLED", _("Disabled (fallback in use)")


class ModelVersion(UUIDModel):
    """Every model or prompt configuration. Add a new row to change it; never edit one in place (Section 9.4)."""

    capability = models.CharField(max_length=12, choices=AICapability.choices)
    provider = models.CharField(max_length=40)
    model_name = models.CharField(max_length=100)
    version = models.CharField(max_length=40, help_text=_("Our own version label, e.g. cls-1.2"))
    confidence_scale = models.CharField(max_length=40, default="0-1")
    low_confidence_threshold = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    config = models.JSONField(default=dict, blank=True, help_text=_("Prompt id, weights, etc."))
    active_from = models.DateTimeField(null=True, blank=True)
    active_to = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ModelStatus.choices, default=ModelStatus.INACTIVE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["capability"], condition=models.Q(status="ACTIVE"),
                                               name="one_active_model_per_capability")]

    def __str__(self) -> str:
        return f"{self.capability} {self.version} ({self.status})"

    def activate(self) -> None:
        now = timezone.now()
        ModelVersion.objects.filter(capability=self.capability, status=ModelStatus.ACTIVE).exclude(pk=self.pk).update(
            status=ModelStatus.INACTIVE, active_to=now)
        self.status, self.active_from, self.active_to = ModelStatus.ACTIVE, now, None
        self.save()

    def disable(self) -> None:
        self.status, self.active_to = ModelStatus.DISABLED, timezone.now()
        self.save(update_fields=["status", "active_to"])

    def is_low_confidence(self, c) -> bool:
        return c is None or (self.low_confidence_threshold is not None and c < self.low_confidence_threshold)


class AIOutcome(models.TextChoices):
    OK = "OK", _("OK")
    LOW_CONFIDENCE = "LOW_CONFIDENCE", _("Low confidence")
    INSUFFICIENT_INPUT = "INSUFFICIENT_INPUT", _("Insufficient input")
    NO_EVIDENCE = "NO_EVIDENCE", _("No evidence")
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION", _("Needs clarification")
    UNAVAILABLE = "UNAVAILABLE", _("Unavailable")
    TIMEOUT = "TIMEOUT", _("Timeout")
    ERROR = "ERROR", _("Error")


class AIInferenceRecord(UUIDModel):
    """One row per AI call (Section 9.7). inputRef is a hash or record reference, never raw personal data."""

    model_version = models.ForeignKey(ModelVersion, null=True, on_delete=models.PROTECT, related_name="inferences")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    capability = models.CharField(max_length=12, choices=AICapability.choices)
    input_ref = models.CharField(max_length=200, blank=True)
    output_summary = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    outcome = models.CharField(max_length=20, choices=AIOutcome.choices)
    user_decision = models.CharField(max_length=10, choices=UserDecision.choices, blank=True)
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def record_decision(self, d: str, reason: str = "") -> None:
        self.user_decision, self.decision_reason = d, reason
        self.save(update_fields=["user_decision", "decision_reason"])


class PolicyDocument(UUIDModel):
    """Policies the assistant may cite (e.g. KU's waste procedure)."""

    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    title = models.CharField(max_length=200)
    version = models.CharField(max_length=40)
    content = models.FileField(upload_to="policies/")
    approved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=RecordStatus.choices, default=RecordStatus.INACTIVE)

    def approve(self, by: User) -> None:
        self.approved_at, self.status = timezone.now(), RecordStatus.ACTIVE
        self.save(update_fields=["approved_at", "status"])

    def retire(self) -> None:
        self.status = RecordStatus.INACTIVE
        self.save(update_fields=["status"])
