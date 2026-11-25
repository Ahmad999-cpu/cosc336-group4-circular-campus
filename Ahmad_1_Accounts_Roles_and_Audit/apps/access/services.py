"""Public interface of the Users & Access module (feature 4.14, UC-42 to UC-45).

Accounts are created by an administrator (the brief allows "user registration or administrator-created
accounts"; a campus system knows its staff, so self-registration is not offered).
Every function checks `admin.users` for the whole institution first, then writes an audit row.
"""
from django.db import transaction

from apps.audit.services import record
from apps.common.errors import ValidationFailed

from .models import AccountStatus, Department, Role, RoleAssignment, User
from .permissions import require


def _snapshot(u: User) -> dict:
    return {"full_name": u.full_name, "email": u.email, "department": str(u.department_id or ""),
            "account_status": u.account_status}


@transaction.atomic
def create_user(by: User, *, full_name: str, email: str, department: Department | None, password: str) -> User:
    require(by, "admin.users")
    email = User.objects.normalize_email(email).lower()
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationFailed("An account with this e-mail already exists")
    user = User.objects.create_user(email, password, full_name=full_name.strip(), department=department)
    record(by, "create_user", "User", user.pk, after=_snapshot(user))
    return user


@transaction.atomic
def update_user(by: User, user: User, *, full_name: str, email: str, department: Department | None) -> User:
    require(by, "admin.users")
    email = User.objects.normalize_email(email).lower()
    if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
        raise ValidationFailed("Another account already uses this e-mail")
    before = _snapshot(user)
    user.full_name, user.email, user.department = full_name.strip(), email, department
    user.save(update_fields=["full_name", "email", "department"])
    record(by, "update_user", "User", user.pk, before=before, after=_snapshot(user))
    return user


def _admins_left_without(user: User) -> int:
    return (RoleAssignment.objects.filter(active=True, scope_department__isnull=True,
                                          role__permissions__code="admin.users", user__account_status=AccountStatus.ACTIVE)
            .exclude(user=user).values("user").distinct().count())


@transaction.atomic
def set_status(by: User, user: User, status: str) -> User:
    """Activate, suspend or deactivate an account (UC-44). Nobody can lock out the last administrator."""
    require(by, "admin.users")
    if status not in AccountStatus.values:
        raise ValidationFailed("Unknown account status")
    if status != AccountStatus.ACTIVE and user.has_role_permission("admin.users") and _admins_left_without(user) == 0:
        raise ValidationFailed("This is the last active administrator; add another one first")
    before = user.account_status
    user.account_status = status
    user.save(update_fields=["account_status"])
    if status != AccountStatus.ACTIVE:
        from .models import SessionStatus
        user.sessions.filter(status=SessionStatus.ACTIVE).update(status=SessionStatus.INVALIDATED)
    record(by, "set_account_status", "User", user.pk, before={"status": before}, after={"status": status})
    return user


@transaction.atomic
def assign_role(by: User, user: User, role: Role, scope: Department | None) -> RoleAssignment:
    """UC-45. Scope empty = the whole institution; otherwise the unit and every unit below it."""
    require(by, "admin.users")
    existing = RoleAssignment.objects.filter(user=user, role=role, scope_department=scope).first()
    if existing and existing.active:
        raise ValidationFailed("This person already has that role for that unit")
    if existing:
        existing.active, existing.assigned_by = True, by
        existing.save(update_fields=["active", "assigned_by"])
        ra = existing
    else:
        ra = RoleAssignment.objects.create(user=user, role=role, scope_department=scope, assigned_by=by)
    record(by, "assign_role", "RoleAssignment", ra.pk,
           after={"user": str(user.pk), "role": role.name, "scope": str(scope or "institution")})
    return ra


@transaction.atomic
def revoke_role(by: User, assignment: RoleAssignment) -> None:
    require(by, "admin.users")
    gives_admin = assignment.role.permits("admin.users") and assignment.scope_department_id is None
    if gives_admin and _admins_left_without(assignment.user) == 0:
        raise ValidationFailed("This is the last administrator role; give it to someone else first")
    assignment.revoke(by)
    record(by, "revoke_role", "RoleAssignment", assignment.pk,
           before={"user": str(assignment.user_id), "role": assignment.role.name, "active": True}, after={"active": False})
