"""Users & Access module (feature 4.14) with the data-driven parts of Institution Blueprint.

Classes from the class diagram: Department, User, Role, RoleAssignment, Session (as UserSession).
Additions for Blueprint: Department.parent / unit_type, Permission, Role.permissions, Role.approval_limit.
"""
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.enums import RecordStatus
from apps.common.models import UUIDModel


class Department(UUIDModel):
    """An organisational unit. With Blueprint, units form a tree (University -> College -> Department -> Lab)."""

    name = models.CharField(max_length=200)
    campus = models.CharField(max_length=100, blank=True)
    building = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=RecordStatus.choices, default=RecordStatus.ACTIVE)
    # Blueprint additions (not in the Phase 5 class diagram):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    unit_type = models.CharField(max_length=50, blank=True, help_text=_("The institution's own word, e.g. College, Lab, Grade"))

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    # --- class diagram operations ---
    def rename(self, name: str) -> None:
        self.name = name
        self.save(update_fields=["name"])

    def deactivate(self) -> None:
        self.status = RecordStatus.INACTIVE
        self.save(update_fields=["status"])

    # --- Blueprint helpers ---
    def ancestors(self) -> list["Department"]:
        chain, node = [], self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        return chain

    def is_within(self, other: "Department") -> bool:
        """True if self is `other` or sits below it in the unit tree."""
        return self.pk == other.pk or any(a.pk == other.pk for a in self.ancestors())


class AccountStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    SUSPENDED = "SUSPENDED", _("Suspended")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)  # Argon2id, salted (NFR-16; see PASSWORD_HASHERS)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("full_name", "System Administrator")
        return self.create_user(email, password, **extra)


class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """Campus user. passwordHash is Django's `password` field; lastLoginAt is Django's `last_login`.

    is_staff / is_superuser only control the developer admin site. Business permissions come from
    RoleAssignment -> Role -> Permission and are checked in services (see access/permissions.py).
    """

    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    account_status = models.CharField(max_length=12, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    created_at = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self) -> str:
        return self.full_name or self.email

    @property
    def is_active(self) -> bool:  # Django reads this to block log-in
        return self.account_status == AccountStatus.ACTIVE

    # --- class diagram operations ---
    def authenticate(self, secret: str) -> bool:
        return self.is_active and self.check_password(secret)

    def has_role(self, role_name: str, dept: Department | None = None) -> bool:
        for ra in self.role_assignments.filter(active=True, role__name=role_name).select_related("role", "scope_department"):
            if dept is None or ra.covers(dept):
                return True
        return False

    def has_role_permission(self, action: str) -> bool:
        """True if any active, institution-wide role of this user grants `action`."""
        return self.role_assignments.filter(active=True, scope_department__isnull=True,
                                            role__permissions__code=action).exists()

    def initials(self) -> str:
        parts = [p for p in self.full_name.split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or self.email[:2].upper()

    def record_login(self, at=None) -> None:
        self.last_login = at or timezone.now()
        self.save(update_fields=["last_login"])

    def deactivate(self) -> None:
        self.account_status = AccountStatus.DEACTIVATED
        self.save(update_fields=["account_status"])


class Permission(models.Model):
    """A basic permission an institution can combine into its own roles (Blueprint 'member types').

    Codes are fixed in code (PERMISSIONS below) because services check them; names are editable.
    """

    code = models.CharField(max_length=60, primary_key=True)
    description = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.code


# The permission codes services check. Seeded by migration / seed_demo.
PERMISSIONS = {
    "asset.register": "Register and edit assets",
    "asset.publish": "Publish and unpublish assets",
    "asset.custody": "Hold custody of assets and confirm their condition",
    "request.submit": "Submit and cancel resource requests",
    "request.approve": "Approve or reject resource requests (up to the role's AED limit)",
    "transfer.dispatch": "Dispatch transfers and record delivery events",
    "transfer.receive": "Confirm receipt of transfers",
    "maintenance.record": "Report defects and record repairs",
    "eol.propose": "Propose end-of-life actions",
    "eol.approve": "Approve end-of-life actions",
    "sustainability.review": "Review sustainable-action advice",
    "reports.view": "View reports and the sustainability dashboard",
    "reports.publish": "Edit and publish AI report summaries",
    "admin.users": "Manage accounts and role assignments",
    "admin.blueprint": "Edit the Institution Blueprint",
    "admin.ai": "Configure AI model versions and thresholds",
}


class Role(UUIDModel):
    """A role (member type). The class diagram used a fixed RoleName enum; Blueprint makes roles data."""

    name = models.CharField(max_length=80, unique=True)
    name_ar = models.CharField(max_length=80, blank=True)
    description = models.CharField(max_length=300, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    approval_limit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Highest asset value (AED) this role may approve. Empty = no limit."),
    )

    def __str__(self) -> str:
        return self.name

    def permits(self, action: str) -> bool:
        return self.permissions.filter(code=action).exists()

    @property
    def display_name(self) -> str:
        from django.utils.translation import get_language
        return self.name_ar if self.name_ar and (get_language() or "").startswith("ar") else self.name


class RoleAssignment(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")  # composition (holds)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="assignments")
    scope_department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.PROTECT, related_name="scoped_assignments",
        help_text=_("Empty = whole institution"),
    )
    assigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    assigned_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def covers(self, dept: Department | None) -> bool:
        """BR-2: authority applies to the scope unit and every unit below it."""
        if not self.active:
            return False
        if self.scope_department_id is None:
            return True
        if dept is None:
            return False
        return dept.is_within(self.scope_department)

    def revoke(self, by: User) -> None:
        self.active = False
        self.save(update_fields=["active"])


class SessionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    INVALIDATED = "INVALIDATED", _("Invalidated")


SESSION_IDLE_LIMIT = timedelta(minutes=15)  # NFR-17


class UserSession(UUIDModel):
    """Session from the class diagram. Django's session framework holds the cookie; this row records
    activity for the 15-minute idle rule and the security audit (NFR-17, NFR-18)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=SessionStatus.choices, default=SessionStatus.ACTIVE)

    def is_expired(self, now=None) -> bool:
        return self.status != SessionStatus.ACTIVE or (now or timezone.now()) >= self.expires_at

    def touch(self, now=None) -> None:
        now = now or timezone.now()
        self.last_activity_at = now
        self.expires_at = now + SESSION_IDLE_LIMIT
        self.save(update_fields=["last_activity_at", "expires_at"])

    def invalidate(self) -> None:
        self.status = SessionStatus.INVALIDATED
        self.save(update_fields=["status"])
