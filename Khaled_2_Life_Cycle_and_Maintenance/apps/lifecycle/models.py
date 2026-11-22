"""Life Cycle & Maintenance module (features 4.9 life-cycle history, 4.10 maintenance, end-of-life approvals).

Classes: LifeCycleEvent, EndOfLifeProposal, MaintenanceRecord, InspectionRequest, RepairAction, MaintenanceUpdate.
State machines: maintenance (Figure 7.9) and end-of-life approval (Figure 7.10).
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.access.models import User
from apps.catalogue.models import Asset, AssetState
from apps.common.enums import Condition, EndOfLifeAction, Urgency
from apps.common.errors import SelfApproval, ValidationFailed
from apps.common.models import UUIDModel
from apps.common.statemachine import move


class EventType(models.TextChoices):
    REGISTRATION = "REGISTRATION", _("Registration")
    UPDATE = "UPDATE", _("Details updated")
    STATE_CHANGE = "STATE_CHANGE", _("State change")
    CONDITION_UPDATE = "CONDITION_UPDATE", _("Condition update")
    PUBLICATION = "PUBLICATION", _("Publication")
    ALLOCATION = "ALLOCATION", _("Allocation")
    TRANSFER = "TRANSFER", _("Transfer")
    INSPECTION = "INSPECTION", _("Inspection")
    MAINTENANCE = "MAINTENANCE", _("Maintenance")
    REPAIR = "REPAIR", _("Repair")
    REFURBISHMENT = "REFURBISHMENT", _("Refurbishment")
    END_OF_LIFE = "END_OF_LIFE", _("End of life")
    CORRECTION = "CORRECTION", _("Correction")


class AppendOnly(models.Model):
    """History rows are never edited or deleted (NFR-27, BR-14). Mistakes are fixed by a correction row."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationFailed(f"{type(self).__name__} is append-only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationFailed(f"{type(self).__name__} is append-only")


class EolStatus(models.TextChoices):
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending review")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ACTION_COMPLETED = "ACTION_COMPLETED", _("Action completed")


EOL_TRANSITIONS = {
    EolStatus.PENDING_REVIEW: {EolStatus.APPROVED, EolStatus.REJECTED},
    EolStatus.APPROVED: {EolStatus.ACTION_COMPLETED},
    EolStatus.REJECTED: set(),
    EolStatus.ACTION_COMPLETED: set(),
}

EOL_ACTIONS = [EndOfLifeAction.RETIRE, EndOfLifeAction.DONATE, EndOfLifeAction.RECYCLE, EndOfLifeAction.DISPOSE]  # list: stable order
EOL_TARGET_STATE = {
    EndOfLifeAction.RETIRE: AssetState.RETIRED,
    EndOfLifeAction.DONATE: AssetState.DONATED,
    EndOfLifeAction.RECYCLE: AssetState.RECYCLED,
    EndOfLifeAction.DISPOSE: AssetState.DISPOSED,
}


class EndOfLifeProposal(UUIDModel):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="eol_proposals")
    proposed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    action_type = models.CharField(max_length=12, choices=[(a.value, a.label) for a in EOL_ACTIONS])
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=EolStatus.choices, default=EolStatus.PENDING_REVIEW, editable=False)
    decision_reason = models.TextField(blank=True)
    proposed_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def approve(self, by: User, reason: str = "") -> None:
        if by.pk == self.proposed_by_id:
            raise SelfApproval("The proposer cannot approve their own proposal (FR-9.22)")
        move(self, "status", EolStatus.APPROVED, EOL_TRANSITIONS)
        self.reviewer, self.decision_reason, self.decided_at = by, reason, timezone.now()
        self.save(update_fields=["status", "reviewer", "decision_reason", "decided_at"])

    def reject(self, by: User, reason: str) -> None:
        if by.pk == self.proposed_by_id:
            raise SelfApproval("The proposer cannot decide their own proposal")
        if not reason.strip():
            raise ValidationFailed("A reason is required")
        move(self, "status", EolStatus.REJECTED, EOL_TRANSITIONS)
        self.reviewer, self.decision_reason, self.decided_at = by, reason, timezone.now()
        self.save(update_fields=["status", "reviewer", "decision_reason", "decided_at"])

    def complete(self, by: User) -> None:
        """Record completion with the approval reference (UC-11): moves the asset to its end-of-life state."""
        move(self, "status", EolStatus.ACTION_COMPLETED, EOL_TRANSITIONS)
        self.save(update_fields=["status"])
        target = EOL_TARGET_STATE[self.action_type]
        if target != AssetState.RETIRED and self.asset.lifecycle_state != AssetState.RETIRED:
            self.asset.change_state(AssetState.RETIRED, by, description="Retired before final action", approval_ref=self)
        self.asset.change_state(target, by, description=f"{self.get_action_type_display()} completed", approval_ref=self)


class LifeCycleEvent(UUIDModel, AppendOnly):
    """One row per thing that happened to an asset: who did what, and when (C6)."""

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="history")
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    corrects = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="corrections")
    approval_ref = models.ForeignKey(EndOfLifeProposal, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    event_date = models.DateField(default=timezone.localdate)
    description = models.TextField(blank=True)
    previous_state = models.CharField(max_length=20, choices=AssetState.choices, blank=True)
    new_state = models.CharField(max_length=20, choices=AssetState.choices, blank=True)
    source_type = models.CharField(max_length=40, blank=True, help_text=_("e.g. Transfer, MaintenanceRecord"))
    source_id = models.UUIDField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["recorded_at"]

    def correction(self, reason: str, by: User) -> "LifeCycleEvent":
        return LifeCycleEvent.objects.create(
            asset=self.asset, recorded_by=by, corrects=self, event_type=EventType.CORRECTION,
            description=reason, previous_state=self.new_state, new_state=self.new_state,
        )


class MaintenanceType(models.TextChoices):
    DEFECT = "DEFECT", _("Defect report")
    INSPECTION = "INSPECTION", _("Inspection request")


class Severity(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class MaintenanceStatus(models.TextChoices):
    DEFECT_REPORTED = "DEFECT_REPORTED", _("Defect reported")
    INSPECTION_REQUESTED = "INSPECTION_REQUESTED", _("Inspection requested")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    REPAIR_COMPLETED = "REPAIR_COMPLETED", _("Repair completed")
    FURTHER_REPAIR_REQUIRED = "FURTHER_REPAIR_REQUIRED", _("Further repair required")
    CLOSED = "CLOSED", _("Closed")


MAINTENANCE_TRANSITIONS = {
    MaintenanceStatus.DEFECT_REPORTED: {MaintenanceStatus.IN_PROGRESS},
    MaintenanceStatus.INSPECTION_REQUESTED: {MaintenanceStatus.IN_PROGRESS},
    MaintenanceStatus.IN_PROGRESS: {MaintenanceStatus.REPAIR_COMPLETED, MaintenanceStatus.FURTHER_REPAIR_REQUIRED},
    MaintenanceStatus.FURTHER_REPAIR_REQUIRED: {MaintenanceStatus.IN_PROGRESS},
    MaintenanceStatus.REPAIR_COMPLETED: {MaintenanceStatus.CLOSED},
    MaintenanceStatus.CLOSED: set(),
}


class MaintenanceRecord(UUIDModel):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="maintenance_records")
    opened_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    record_type = models.CharField(max_length=12, choices=MaintenanceType.choices)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    discovery_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=25, choices=MaintenanceStatus.choices, editable=False)
    current_condition = models.CharField(max_length=10, choices=Condition.choices)
    opened_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.status:
            self.status = (MaintenanceStatus.INSPECTION_REQUESTED if self.record_type == MaintenanceType.INSPECTION
                           else MaintenanceStatus.DEFECT_REPORTED)
        super().save(*args, **kwargs)

    def transition_to(self, s: str, by: User, notes: str = "", condition: str | None = None) -> None:
        previous = move(self, "status", s, MAINTENANCE_TRANSITIONS)
        if condition:
            self.current_condition = condition
        self.save(update_fields=["status", "current_condition"])
        MaintenanceUpdate.objects.create(maintenance=self, updated_by=by, previous_status=previous, new_status=s,
                                         condition=self.current_condition, notes=notes)

    def add_repair(self, r: "RepairAction", by: User) -> None:
        """Record a repair and move to Repair Completed / Further Repair Required (UC-15).
        Repair Completed does NOT make the asset available again (FR-10.18)."""
        if self.status != MaintenanceStatus.IN_PROGRESS:
            raise ValidationFailed("Start work before recording a repair")
        r.maintenance = self
        r.save()
        self.transition_to(MaintenanceStatus.REPAIR_COMPLETED if r.is_successful() else MaintenanceStatus.FURTHER_REPAIR_REQUIRED, by)

    def is_open(self) -> bool:
        return self.status != MaintenanceStatus.CLOSED


class InspectionStatus(models.TextChoices):
    REQUESTED = "REQUESTED", _("Requested")
    FINDINGS_RECORDED = "FINDINGS_RECORDED", _("Findings recorded")
    CLOSED = "CLOSED", _("Closed")


class InspectionRequest(UUIDModel):
    maintenance = models.OneToOneField(MaintenanceRecord, on_delete=models.CASCADE, related_name="inspection")
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    reason = models.TextField()
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.MEDIUM)
    preferred_date = models.DateField(null=True, blank=True)
    findings = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=InspectionStatus.choices, default=InspectionStatus.REQUESTED)

    def record_findings(self, text: str) -> None:
        self.findings, self.status = text, InspectionStatus.FINDINGS_RECORDED
        self.save(update_fields=["findings", "status"])

    def close(self) -> None:
        self.status = InspectionStatus.CLOSED
        self.save(update_fields=["status"])


class RepairOutcome(models.TextChoices):
    SUCCESSFUL = "SUCCESSFUL", _("Successful")
    UNSUCCESSFUL = "UNSUCCESSFUL", _("Unsuccessful")


class RepairAction(UUIDModel):
    maintenance = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name="repairs")
    technician = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    description = models.TextField()
    actions_performed = models.TextField(blank=True)
    repair_date = models.DateField(default=timezone.localdate)
    outcome = models.CharField(max_length=12, choices=RepairOutcome.choices)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="AED")
    recorded_at = models.DateTimeField(auto_now_add=True)

    def is_successful(self) -> bool:
        return self.outcome == RepairOutcome.SUCCESSFUL


class MaintenanceUpdate(UUIDModel):
    maintenance = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name="updates")
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    previous_status = models.CharField(max_length=25, choices=MaintenanceStatus.choices)
    new_status = models.CharField(max_length=25, choices=MaintenanceStatus.choices)
    condition = models.CharField(max_length=10, choices=Condition.choices)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)
