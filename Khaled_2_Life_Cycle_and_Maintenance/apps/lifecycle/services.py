"""Public interface of the Life Cycle & Maintenance module (features 4.9 and 4.10; lab C6).

C6: "Allow only the moves in the cycle. Show for each asset who did what, and when."
Every change here writes a LifeCycleEvent in the same transaction (BR-10), and every asset state change goes
through the Asset entity, which enforces Figure 7.5.
"""
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext_lazy as _l

from apps.access.models import User
from apps.access.permissions import can, require, units_for, users_who_can
from apps.audit.services import record
from apps.catalogue.models import ASSET_TRANSITIONS, Asset, AssetState
from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import NotificationType
from apps.notifications.services import Msg, enqueue

from .models import (EndOfLifeProposal, EolStatus, EventType, InspectionRequest, LifeCycleEvent, MaintenanceRecord,
                     MaintenanceStatus, MaintenanceType, RepairAction)

OPEN_MAINTENANCE = [MaintenanceStatus.DEFECT_REPORTED, MaintenanceStatus.INSPECTION_REQUESTED, MaintenanceStatus.IN_PROGRESS,
                    MaintenanceStatus.FURTHER_REPAIR_REQUIRED, MaintenanceStatus.REPAIR_COMPLETED]


def _event(asset, by, event_type, description, source=None):
    return LifeCycleEvent.objects.create(asset=asset, recorded_by=by, event_type=event_type, description=description,
                                         previous_state=asset.lifecycle_state, new_state=asset.lifecycle_state,
                                         source_type=type(source).__name__ if source else "", source_id=getattr(source, "pk", None))


def _lock(asset) -> Asset:
    return Asset.objects.select_for_update().get(pk=asset.pk)


# ---------------------------------------------------------------- history (C6)

def history(asset: Asset):
    return asset.history.select_related("recorded_by", "corrects", "approval_ref").order_by("-recorded_at")


def next_states(asset: Asset) -> list[str]:
    """The moves the state machine allows from here (shown on the history page)."""
    return sorted(ASSET_TRANSITIONS.get(asset.lifecycle_state, set()))


@transaction.atomic
def correct_event(by: User, event: LifeCycleEvent, reason: str) -> LifeCycleEvent:
    """History is append-only; a mistake is fixed by a correction that points at the wrong row (NFR-27)."""
    require(by, "asset.register", event.asset.owner_department)
    if not reason.strip():
        raise ValidationFailed("Say what was wrong")
    c = event.correction(reason.strip(), by)
    record(by, "correct_history", "LifeCycleEvent", event.pk, after={"correction": str(c.pk), "reason": reason})
    return c


# ---------------------------------------------------------------- maintenance (feature 4.10)

def _may_maintain(by, asset):
    if not can(by, "maintenance.record", asset.owner_department):
        raise Forbidden("Only maintenance staff or the unit's custodians can do this")


@transaction.atomic
def report_problem(by: User, asset: Asset, *, description: str, severity: str, condition: str,
                   inspection: bool = False, urgency: str = "MEDIUM", preferred_date=None) -> MaintenanceRecord:
    """UC-13 (defect) / UC-14 (inspection). One open record per asset at a time."""
    asset = _lock(asset)
    _may_maintain(by, asset)
    if MaintenanceRecord.objects.filter(asset=asset, status__in=OPEN_MAINTENANCE).exists():
        raise ValidationFailed("This asset already has an open maintenance record")
    if not description.strip():
        raise ValidationFailed("Describe the problem")
    rec = MaintenanceRecord.objects.create(asset=asset, opened_by=by, description=description.strip(), severity=severity,
                                           record_type=MaintenanceType.INSPECTION if inspection else MaintenanceType.DEFECT,
                                           current_condition=condition)
    if inspection:
        InspectionRequest.objects.create(maintenance=rec, requested_by=by, reason=description.strip(), urgency=urgency, preferred_date=preferred_date)
    _event(asset, by, EventType.INSPECTION if inspection else EventType.MAINTENANCE,
           ("Inspection requested: " if inspection else "Defect reported: ") + description.strip(), rec)
    if condition != asset.condition:
        asset.update_condition(condition, by)
    for tech in users_who_can("maintenance.record", asset.owner_department):
        if tech.pk != by.pk:
            enqueue(tech, NotificationType.MAINTENANCE_UPDATE,
                    Msg(_l("New inspection request: %(name)s (%(sev)s).") if inspection else _l("New defect: %(name)s (%(sev)s)."),
                        name=asset.name, sev=rec.get_severity_display), f"MaintenanceRecord:{rec.pk}")
    record(by, "report_problem", "MaintenanceRecord", rec.pk, after={"asset": str(asset.pk), "severity": severity})
    return rec


@transaction.atomic
def start_work(by: User, rec: MaintenanceRecord, notes: str = "") -> MaintenanceRecord:
    """UC-16. The asset leaves the marketplace for maintenance; refused while units are reserved (no commitments)."""
    rec = MaintenanceRecord.objects.select_for_update().get(pk=rec.pk)
    asset = _lock(rec.asset)
    _may_maintain(by, asset)
    if asset.lifecycle_state != AssetState.UNDER_MAINTENANCE:
        if asset.reserved_quantity > 0:
            raise ValidationFailed("Units are reserved for a transfer; finish or cancel it first")
        asset.change_state(AssetState.UNDER_MAINTENANCE, by, description="Maintenance started", source=rec)
    rec.transition_to(MaintenanceStatus.IN_PROGRESS, by, notes)
    if hasattr(rec, "inspection") and notes:
        rec.inspection.record_findings(notes)
    return rec


@transaction.atomic
def record_repair(by: User, rec: MaintenanceRecord, *, description: str, actions: str, outcome: str, cost: Decimal) -> RepairAction:
    """UC-15. Successful -> Repair completed; unsuccessful -> Further repair required. The asset stays Under
    maintenance until a custodian confirms it can go back into service (FR-10.18)."""
    rec = MaintenanceRecord.objects.select_for_update().get(pk=rec.pk)
    _may_maintain(by, rec.asset)
    if cost is None or cost < 0:
        raise ValidationFailed("Cost cannot be negative")
    repair = RepairAction(technician=by, description=description.strip() or "Repair", actions_performed=actions, outcome=outcome, cost=cost)
    rec.add_repair(repair, by)
    _event(rec.asset, by, EventType.REPAIR, f"Repair {'successful' if repair.is_successful() else 'unsuccessful'}: {repair.description} (AED {cost})", rec)
    enqueue(rec.opened_by, NotificationType.MAINTENANCE_UPDATE,
            Msg(_l("%(name)s: repair done, waiting for the custodian to return it to service.") if repair.is_successful()
                else _l("%(name)s: repair unsuccessful, more work needed."), name=rec.asset.name),
            f"MaintenanceRecord:{rec.pk}")
    return repair


@transaction.atomic
def return_to_service(by: User, rec: MaintenanceRecord, condition: str) -> Asset:
    """UC-12 after a repair: the custodian checks the item and makes it Available again; the record closes."""
    rec = MaintenanceRecord.objects.select_for_update().get(pk=rec.pk)
    asset = _lock(rec.asset)
    require(by, "asset.custody", asset.owner_department)
    if rec.status != MaintenanceStatus.REPAIR_COMPLETED:
        raise ValidationFailed("Record a successful repair first")
    rec.transition_to(MaintenanceStatus.CLOSED, by, "Returned to service", condition)
    if condition != asset.condition:
        asset.update_condition(condition, by)
    if asset.lifecycle_state == AssetState.UNDER_MAINTENANCE:
        asset.change_state(AssetState.AVAILABLE, by, description="Back in service after repair", source=rec)
    return asset


def maintenance_for(user: User):
    units = units_for(user, "maintenance.record")
    return (MaintenanceRecord.objects.filter(asset__owner_department__in=units)
            .select_related("asset", "asset__owner_department", "opened_by").prefetch_related("repairs"))


def open_maintenance_count(user: User) -> int:
    return maintenance_for(user).filter(status__in=OPEN_MAINTENANCE).count()


# ---------------------------------------------------------------- end of life (UC-11, UC-49)

@transaction.atomic
def propose_end_of_life(by: User, asset: Asset, action: str, reason: str) -> EndOfLifeProposal:
    asset = _lock(asset)
    require(by, "eol.propose", asset.owner_department)
    if asset.reserved_quantity > 0:
        raise ValidationFailed("Units are reserved for a transfer; no end-of-life action while there are commitments")
    if asset.lifecycle_state not in (AssetState.AVAILABLE, AssetState.UNDER_MAINTENANCE, AssetState.RETIRED, AssetState.REGISTERED):
        raise ValidationFailed("This asset cannot be retired from its current state")
    if EndOfLifeProposal.objects.filter(asset=asset, status__in=[EolStatus.PENDING_REVIEW, EolStatus.APPROVED]).exists():
        raise ValidationFailed("There is already an open proposal for this asset")
    if not reason.strip():
        raise ValidationFailed("Give a reason")
    p = EndOfLifeProposal.objects.create(asset=asset, proposed_by=by, action_type=action, reason=reason.strip())
    _event(asset, by, EventType.END_OF_LIFE, f"Proposed: {p.get_action_type_display()}. {reason.strip()}", p)
    for reviewer in users_who_can("eol.approve", asset.owner_department):
        if reviewer.pk != by.pk:
            enqueue(reviewer, NotificationType.OTHER,
                    Msg(_l("End-of-life proposal: %(action)s %(name)s."), action=p.get_action_type_display, name=asset.name),
                    f"EndOfLifeProposal:{p.pk}")
    record(by, "propose_end_of_life", "EndOfLifeProposal", p.pk, after={"asset": str(asset.pk), "action": action})
    return p


@transaction.atomic
def decide_end_of_life(by: User, proposal: EndOfLifeProposal, approve: bool, reason: str = "") -> EndOfLifeProposal:
    """UC-49. An independent reviewer: the proposer cannot decide (the model refuses, FR-9.22)."""
    p = EndOfLifeProposal.objects.select_for_update().get(pk=proposal.pk)
    require(by, "eol.approve", p.asset.owner_department)
    if approve:
        p.approve(by, reason)
    else:
        p.reject(by, reason)
    _event(p.asset, by, EventType.END_OF_LIFE, f"{'Approved' if approve else 'Rejected'}: {p.get_action_type_display()}{'. ' + reason if reason else ''}", p)
    enqueue(p.proposed_by, NotificationType.OTHER,
            Msg(_l("%(action)s %(name)s: approved, record it when done.") if approve else _l("%(action)s %(name)s: rejected. %(reason)s"),
                action=p.get_action_type_display, name=p.asset.name, reason=reason), f"EndOfLifeProposal:{p.pk}")
    record(by, "decide_end_of_life", "EndOfLifeProposal", p.pk, after={"approved": approve, "reason": reason})
    return p


@transaction.atomic
def complete_end_of_life(by: User, proposal: EndOfLifeProposal) -> Asset:
    """UC-11: the custodian records that the approved action happened; the asset moves to its final state."""
    p = EndOfLifeProposal.objects.select_for_update().get(pk=proposal.pk)
    asset = _lock(p.asset)
    require(by, "asset.custody", asset.owner_department)
    if asset.reserved_quantity > 0:
        raise ValidationFailed("Units are reserved for a transfer")
    p.asset = asset
    p.complete(by)
    record(by, "complete_end_of_life", "EndOfLifeProposal", p.pk, after={"state": asset.lifecycle_state})
    return asset


def proposals_for(user: User):
    units = list(units_for(user, "eol.approve")) + list(units_for(user, "eol.propose"))
    return (EndOfLifeProposal.objects.filter(asset__owner_department__in=units)
            .select_related("asset", "asset__owner_department", "proposed_by", "reviewer").distinct())


def attention_count(user: User) -> int:
    """Menu badge: open maintenance plus proposals this person can decide."""
    units = units_for(user, "eol.approve")
    eol = EndOfLifeProposal.objects.filter(asset__owner_department__in=units, status=EolStatus.PENDING_REVIEW).exclude(proposed_by=user).count()
    return open_maintenance_count(user) + eol

