"""Reporting module (feature 4.13; C9 basic report with CSV, AI feature 5 generated summary).

Classes: Report, AISummary. Totals are always computed by the database; the AI only writes a draft
summary that a person edits before publishing (FR-15.13).
"""
import csv
import io

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.ai.models import ModelVersion
from apps.common.errors import ValidationFailed
from apps.common.models import UUIDModel


class ReportType(models.TextChoices):
    REQUESTS_TRANSFERS = "REQUESTS_TRANSFERS", _("Requests and transfers")
    AVAILABLE_ASSETS = "AVAILABLE_ASSETS", _("Available assets")
    MAINTENANCE = "MAINTENANCE", _("Maintenance history")
    SUSTAINABILITY = "SUSTAINABILITY", _("Sustainability")
    AI_QUALITY = "AI_QUALITY", _("AI quality")


class Report(UUIDModel):
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reports")
    report_type = models.CharField(max_length=24, choices=ReportType.choices)
    filters = models.JSONField(default=dict, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    data_cutoff = models.DateTimeField(default=timezone.now)
    generated_at = models.DateTimeField(auto_now_add=True)
    exported_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def to_csv(cols: list[str], rows: list[dict]) -> str:
        """C9 CSV export. Rows come from the report query in reporting/services.py."""
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()

    def mark_exported(self, at=None) -> None:
        self.exported_at = at or timezone.now()
        self.save(update_fields=["exported_at"])


class SummaryStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACCEPTED = "ACCEPTED", _("Published")
    REJECTED = "REJECTED", _("Rejected")


class AISummary(UUIDModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="summaries")
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="+")
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    draft_text = models.TextField()
    final_text = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=SummaryStatus.choices, default=SummaryStatus.DRAFT)
    generated_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def edit(self, text: str) -> None:
        if self.status != SummaryStatus.DRAFT:
            raise ValidationFailed("Only drafts can be edited")
        self.final_text = text
        self.save(update_fields=["final_text"])

    def accept(self, text: str, by: User) -> None:
        if self.status != SummaryStatus.DRAFT:
            raise ValidationFailed("Already decided")
        self.final_text, self.status, self.reviewed_by, self.reviewed_at = text, SummaryStatus.ACCEPTED, by, timezone.now()
        self.save()

    def reject(self, by: User) -> None:
        if self.status != SummaryStatus.DRAFT:
            raise ValidationFailed("Already decided")
        self.status, self.reviewed_by, self.reviewed_at = SummaryStatus.REJECTED, by, timezone.now()
        self.save()
