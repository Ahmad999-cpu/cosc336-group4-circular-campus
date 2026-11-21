"""Decides who may approve a request, from the Blueprint's approval rules."""
from apps.access.models import Department, Role
from apps.catalogue.models import Asset

from .models import ApprovalRule, ApproverScope


def approval_route(asset: Asset, quantity: int) -> tuple[Role, Department | None] | None:
    """Return (role, unit) that must approve, or None if no rule matches.

    With no matching rule the Approvals module falls back to 'any user with request.approve covering the
    owning department', so a fresh install works before the Blueprint is set up.
    """
    value = asset.estimated_value * quantity if asset.estimated_value is not None else None
    for rule in ApprovalRule.objects.filter(active=True).select_related("category", "approver_role"):
        if rule.matches(asset.category, value):
            unit = asset.owner_department
            if rule.approver_scope == ApproverScope.PARENT_UNIT:
                unit = unit.parent or unit
            elif rule.approver_scope == ApproverScope.INSTITUTION:
                unit = None
            return rule.approver_role, unit
    return None
