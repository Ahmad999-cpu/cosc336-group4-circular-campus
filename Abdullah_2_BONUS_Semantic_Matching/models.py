"""Matching Orchestration module (feature 4.12 AI-based matching; lab AI feature 2, required).

Classes: MatchResultSet, MatchRecommendation, plus EmbeddingIndex (pgvector store, not a class-diagram entity).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from pgvector.django import HnswIndex, VectorField

from apps.access.models import User
from apps.ai.models import ModelVersion
from apps.catalogue.models import Asset
from apps.common.enums import UserDecision
from apps.common.models import UUIDModel
from apps.resource_requests.models import ResourceRequest

EMBEDDING_DIM = 384  # paraphrase-multilingual-MiniLM-L12-v2 (Arabic + English)
SUITABLE_SCORE = 70  # Section 9.2: >= 70 suitable, 55-69 weak, < 55 hidden
WEAK_SCORE = 55


class ResultSetStatus(models.TextChoices):
    CURRENT = "CURRENT", _("Current")
    SUPERSEDED = "SUPERSEDED", _("Superseded")


class MatchResultSet(UUIDModel):
    # A result set is either for a saved request, or for a free-text search on the Find page (request empty).
    request = models.ForeignKey(ResourceRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="match_sets")
    query_text = models.TextField(blank=True)
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="+")
    generated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    generated_at = models.DateTimeField(auto_now_add=True)
    input_snapshot_ref = models.CharField(max_length=80)
    status = models.CharField(max_length=12, choices=ResultSetStatus.choices, default=ResultSetStatus.CURRENT)

    class Meta:
        ordering = ["-generated_at"]

    def top_pick(self) -> "MatchRecommendation | None":
        return self.recommendations.filter(compatibility_score__gte=SUITABLE_SCORE).order_by("rank").first()

    def is_current(self, snapshot: str) -> bool:
        return self.status == ResultSetStatus.CURRENT and self.input_snapshot_ref == snapshot

    def supersede(self) -> None:
        self.status = ResultSetStatus.SUPERSEDED
        self.save(update_fields=["status"])


class MatchRecommendation(UUIDModel):
    result_set = models.ForeignKey(MatchResultSet, on_delete=models.CASCADE, related_name="recommendations")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="recommended_in")
    rank = models.PositiveIntegerField()
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100, NOT a probability
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    factor_scores = models.JSONField(default=dict)  # {"f1": 0.9, ...} and contributions
    explanation = models.TextField()
    estimate_notes = models.TextField(blank=True)
    user_decision = models.CharField(max_length=10, choices=UserDecision.choices, blank=True)
    decision_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["rank"]

    def summarize(self) -> str:
        return f"#{self.rank} {self.asset.name} · score {self.compatibility_score:.0f} · {self.explanation.splitlines()[0] if self.explanation else ''}"

    def is_weak(self) -> bool:
        return self.compatibility_score < SUITABLE_SCORE

    def record_decision(self, d: str, reason: str = "") -> None:
        self.user_decision, self.decision_reason = d, reason
        self.save(update_fields=["user_decision", "decision_reason"])


class EmbeddedKind(models.TextChoices):
    ASSET = "ASSET", _("Asset")
    REQUEST = "REQUEST", _("Request")


class EmbeddingIndex(models.Model):
    """Vectors live in a table this module owns, so Catalogue and Requests never depend on pgvector."""

    kind = models.CharField(max_length=8, choices=EmbeddedKind.choices)
    object_id = models.UUIDField()
    embedding = VectorField(dimensions=EMBEDDING_DIM)
    text_hash = models.CharField(max_length=64, help_text=_("Re-embed only when the text changed"))
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["kind", "object_id"], name="uniq_embedding_per_object")]
        indexes = [HnswIndex(name="embedding_hnsw", fields=["embedding"], opclasses=["vector_cosine_ops"])]


# ----------------------------------------------------------------------------- Phase 5: saved needs (wishlist)

class NeedStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")


class SavedNeed(UUIDModel):
    """A need saved when nothing suitable is free yet. Checked whenever an item is published or becomes free
    again; matches are explained and notified, never requested or reserved. Visible only to its owner.

    `asset` set = interest in one specific coming-soon item (Phase 6): an expression of interest, not a reservation."""

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_needs")
    department = models.ForeignKey("access.Department", on_delete=models.PROTECT, related_name="+")
    description = models.CharField(max_length=300)
    category = models.ForeignKey("catalogue.Category", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    quantity = models.PositiveIntegerField(default=1)
    specifications = models.CharField(max_length=300, blank=True)
    preferred_condition = models.CharField(max_length=10, default="ANY")
    campus = models.CharField(max_length=100, blank=True)
    needed_by = models.DateField(null=True, blank=True)
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.CASCADE, related_name="interests")
    status = models.CharField(max_length=8, choices=NeedStatus.choices, default=NeedStatus.ACTIVE)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    check_failed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]
        constraints = [models.UniqueConstraint(fields=["owner", "asset"], condition=models.Q(asset__isnull=False),
                                               name="one_interest_per_person_and_asset")]

    def __str__(self) -> str:
        return self.description

    @property
    def is_interest(self) -> bool:
        return self.asset_id is not None


class NeedMatch(UUIDModel):
    """The latest match of one saved need with one asset. `signature` holds what the person was told
    (free units covered, condition, score band); the same signature is never notified twice."""

    need = models.ForeignKey(SavedNeed, on_delete=models.CASCADE, related_name="matches")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="need_matches")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    covered = models.PositiveIntegerField()
    explanation = models.TextField()
    signature = models.CharField(max_length=80)
    notified_signature = models.CharField(max_length=80, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["need", "asset"], name="uniq_need_asset_match")]
        ordering = ["-score"]

    @property
    def partial(self) -> bool:
        return self.covered < self.need.quantity

    def is_weak(self) -> bool:
        return self.score < SUITABLE_SCORE
