"""Server-side permission checks (C1: hiding a button is not enough).

Every service function that changes data calls `require(...)` before doing anything.
Views may call `can(...)` to decide what to show, but the service check is the one that counts.
"""
from decimal import Decimal

from apps.common.errors import Forbidden

from .models import Department, RoleAssignment, User


def _assignments(user: User, action: str):
    return (
        RoleAssignment.objects.filter(user=user, active=True, role__permissions__code=action)
        .select_related("role", "scope_department")
        .distinct()
    )


def can(user: User, action: str, dept: Department | None = None, *, value: Decimal | None = None) -> bool:
    """True if one of the user's active role assignments permits `action` for `dept`.

    `value` (AED) is checked against Role.approval_limit, which Blueprint uses for approval limits.
    Superusers get no business shortcut: the System Administrator needs an assigned role to approve.
    """
    if user is None or not user.is_authenticated or not user.is_active:
        return False
    for ra in _assignments(user, action):
        if not ra.covers(dept):
            continue
        limit = ra.role.approval_limit
        if value is not None and limit is not None and value > limit:
            continue
        return True
    return False


def has_any(user: User, action: str) -> bool:
    """True if the user may do `action` somewhere (in any unit). Used to decide what to show in menus;
    services still call `require` with the real department."""
    if user is None or not user.is_authenticated or not user.is_active:
        return False
    return _assignments(user, action).exists()


def units_for(user: User, action: str):
    """Departments where `user` may do `action` (a scoped role covers its unit and every unit below it).
    Returns a queryset of active departments, ordered by name."""
    if user is None or not user.is_authenticated or not user.is_active:
        return Department.objects.none()
    scopes = list(_assignments(user, action).values_list("scope_department_id", flat=True))
    if not scopes:
        return Department.objects.none()
    if None in scopes:
        return Department.objects.filter(status="ACTIVE").order_by("name")
    ids, frontier = set(scopes), list(scopes)
    while frontier:
        frontier = list(Department.objects.filter(parent_id__in=frontier).exclude(pk__in=ids).values_list("pk", flat=True))
        ids.update(frontier)
    return Department.objects.filter(pk__in=ids, status="ACTIVE").order_by("name")


def users_who_can(action: str, dept: Department | None):
    """Active people whose role permits `action` for `dept` (used to address notifications)."""
    found = []
    for ra in (RoleAssignment.objects.filter(active=True, role__permissions__code=action, user__account_status="ACTIVE")
               .select_related("user", "scope_department", "role").distinct()):
        if ra.covers(dept) and ra.user not in found:
            found.append(ra.user)
    return found


def require(user: User, action: str, dept: Department | None = None, *, value: Decimal | None = None) -> None:
    if not can(user, action, dept, value=value):
        # The audit module records denied attempts; import here to keep access free of upward imports.
        from apps.audit.services import record

        record(actor=user if getattr(user, "is_authenticated", False) else None, action=f"DENIED:{action}",
               entity_type="Department", entity_id=getattr(dept, "pk", None), outcome="DENIED")
        raise Forbidden(f"Not permitted: {action}")
