"""Sustainability module (feature 4.11 sustainability recommendations; measures for C7 and UC-40).

Classes: SustainabilityRecommendation (state machine Figure 7.11), SustainabilityImpact, EmissionFactor.
Numbers come from deterministic formulas (calculator.py); AI only suggests actions.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.ai.models import ModelVersion
from apps.catalogue.models import Asset, Category
from apps.common.enums import EndOfLifeAction
from apps.common.errors import ValidationFailed
from apps.common.models import UUIDModel
from apps.common.statemachine import move
from apps.transfers.models import Transfer


class RecommendationStatus(models.TextChoices):
    UNDECIDED = "UNDECIDED", _("Undecided")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")
    OUTDATED = "OUTDATED", _("Outdated")


RECOMMENDATION_TRANSITIONS = {
    RecommendationStatus.UNDECIDED: {RecommendationStatus.ACCEPTED, RecommendationStatus.REJECTED, RecommendationStatus.OUTDATED},
    RecommendationStatus.ACCEPTED: set(),
    RecommendationStatus.REJECTED: set(),
    RecommendationStatus.OUTDATED: set(),
}


class SustainabilityRecommendation(UUIDModel):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="sustainability_recommendations")
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="+")
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    recommended_action = models.CharField(max_length=12, choices=EndOfLifeAction.choices)
    explanation = models.TextField()
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    input_snapshot_ref = models.CharField(max_length=80)
    estimate_assumptions = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=RecommendationStatus.choices, default=RecommendationStatus.UNDECIDED, editable=False)
    decision_reason = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def is_current(self, snapshot: str) -> bool:
        return self.input_snapshot_ref == snapshot

    def accept(self, by: User) -> None:
        move(self, "status", RecommendationStatus.ACCEPTED, RECOMMENDATION_TRANSITIONS)
        self.decided_by, self.decided_at = by, timezone.now()
        self.save(update_fields=["status", "decided_by", "decided_at"])

    def reject(self, by: User, reason: str) -> None:
        if not reason.strip():
            raise ValidationFailed("A reason is required")
        move(self, "status", RecommendationStatus.REJECTED, RECOMMENDATION_TRANSITIONS)
        self.decided_by, self.decided_at, self.decision_reason = by, timezone.now(), reason
        self.save(update_fields=["status", "decided_by", "decided_at", "decision_reason"])

    def mark_outdated(self) -> None:
        move(self, "status", RecommendationStatus.OUTDATED, RECOMMENDATION_TRANSITIONS)
        self.save(update_fields=["status"])


class EmissionFactor(UUIDModel):
    """A locally selected carbon factor. Source and date are required so every figure can be traced (BR-15)."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="emission_factors")
    kg_co2e_per_unit = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20, default="item")
    source = models.CharField(max_length=300)
    source_date = models.DateField()
    boundary = models.CharField(max_length=100, blank=True, help_text=_("e.g. cradle-to-gate"))
    # Design change 16: waste diverted needs a typical mass per unit. Optional: missing mass = "unavailable".
    mass_kg_per_unit = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                           help_text=_("Typical mass of one unit, for waste diverted"))

    class Meta:
        ordering = ["category__name", "-source_date"]

    def __str__(self) -> str:
        return f"{self.category} · {self.kg_co2e_per_unit} kg CO2e/{self.unit}"

    def applies_to(self, category_id) -> bool:
        return category_id in Category.objects.get(pk=self.category_id).descendant_ids()


class ImpactType(models.TextChoices):
    AVOIDED_PURCHASE = "AVOIDED_PURCHASE", _("Estimated avoided purchase")
    VERIFIED_AVOIDED_PURCHASE = "VERIFIED_AVOIDED_PURCHASE", _("Verified avoided purchase")
    WASTE_DIVERSION = "WASTE_DIVERSION", _("Waste diverted")
    CARBON_REDUCTION = "CARBON_REDUCTION", _("Carbon reduction")
    LIFE_EXTENSION = "LIFE_EXTENSION", _("Asset life extension")


class SustainabilityImpact(UUIDModel):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="impacts")
    transfer = models.ForeignKey(Transfer, null=True, blank=True, on_delete=models.PROTECT, related_name="impacts")
    factor = models.ForeignKey(EmissionFactor, null=True, blank=True, on_delete=models.PROTECT, related_name="impacts")
    impact_type = models.CharField(max_length=30, choices=ImpactType.choices)
    units = models.PositiveIntegerField(default=1)  # design change 16: units the figure covers (for coverage)
    avoided_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # AED
    mass_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    co2e_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assumptions = models.TextField()
    is_estimate = models.BooleanField(default=True)
    calculated_at = models.DateTimeField(auto_now=True)

    def recalculate(self, f: EmissionFactor, units: int = 1) -> None:
        """Carbon reduction = new-asset emissions avoided (Section 9.6). Missing data stays None, never 0."""
        self.factor = f
        self.co2e_kg = f.kg_co2e_per_unit * units
        self.assumptions = f"{units} unit(s) × {f.kg_co2e_per_unit} kg CO2e/{f.unit}; source: {f.source} ({f.source_date})"
        self.save()
