"""Institution Blueprint (bonus feature): the institution describes its structure once and the platform
reads its rules from here instead of hard-coded logic.

Already data-driven elsewhere: units (access.Department.parent / unit_type), member types
(access.Role + Permission + approval_limit). This module adds approval routes and the AI-drafted setup.
Visibility rings and priority rules are planned (see docs/modules/blueprint.md).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.access.models import Role, User
from apps.catalogue.models import Category
from apps.common.models import UUIDModel


class ApproverScope(models.TextChoices):
    OWNING_UNIT = "OWNING_UNIT", _("Unit that owns the asset")
    PARENT_UNIT = "PARENT_UNIT", _("Parent of the owning unit")
    INSTITUTION = "INSTITUTION", _("Anyone in the institution with the role")


class ApprovalRule(UUIDModel):
    """'Under AED 2,000 -> Head of Department. IT equipment -> IT first.' Rules are checked by priority;
    the first one that matches decides who approves. One approval step per request in this version."""

    name = models.CharField(max_length=120)
    priority = models.PositiveIntegerField(default=100, help_text=_("Lower number is checked first"))
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT,
                                 help_text=_("Applies to this category and its children. Empty = any category"))
    min_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    approver_role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="approval_rules")
    approver_scope = models.CharField(max_length=12, choices=ApproverScope.choices, default=ApproverScope.OWNING_UNIT)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self) -> str:
        return self.name

    def matches(self, category: Category, value) -> bool:
        if not self.active:
            return False
        if self.category_id and category.pk not in self.category.descendant_ids():
            return False
        if value is not None:
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        return True


class DraftStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    DISCARDED = "DISCARDED", _("Discarded")


class BlueprintDraft(UUIDModel):
    """AI-assisted setup: the admin describes the institution in plain words, the AI drafts units, roles and
    rules as JSON, the admin edits and publishes. Publishing writes the normal tables; the AI never does."""

    description = models.TextField(help_text=_("The admin's plain-words description"))
    draft = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=DraftStatus.choices, default=DraftStatus.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    published_at = models.DateTimeField(null=True, blank=True)
    inference_id = models.UUIDField(null=True, blank=True)
