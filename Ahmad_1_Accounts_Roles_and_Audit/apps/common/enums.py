"""Enumeration types shared by several modules (class diagram types such as Condition, Urgency)."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Condition(models.TextChoices):
    # Ordered best -> worst. The design document does not list the values; these are a proposal (see docs).
    NEW = "NEW", _("New")
    GOOD = "GOOD", _("Good")
    FAIR = "FAIR", _("Fair")
    POOR = "POOR", _("Poor")

    @classmethod
    def rank(cls, value: str) -> int:
        """Higher is better: NEW=3 ... POOR=0."""
        order = [cls.POOR, cls.FAIR, cls.GOOD, cls.NEW]
        return order.index(value)


class PreferredCondition(models.TextChoices):
    """A request may accept any condition (Table 9.2, f3: 'Any' -> 1)."""

    ANY = "ANY", _("Any")
    NEW = Condition.NEW.value, Condition.NEW.label
    GOOD = Condition.GOOD.value, Condition.GOOD.label
    FAIR = Condition.FAIR.value, Condition.FAIR.label
    POOR = Condition.POOR.value, Condition.POOR.label


class Urgency(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")


class RecordStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")


class EndOfLifeAction(models.TextChoices):
    """Sustainable actions from the project brief (used by recommendations and end-of-life proposals)."""

    RETAIN = "RETAIN", _("Retain")
    TRANSFER = "TRANSFER", _("Transfer")
    REPAIR = "REPAIR", _("Repair")
    REFURBISH = "REFURBISH", _("Refurbish")
    RETIRE = "RETIRE", _("Retire")
    DONATE = "DONATE", _("Donate")
    DISASSEMBLE = "DISASSEMBLE", _("Disassemble for components")
    RECYCLE = "RECYCLE", _("Recycle")
    DISPOSE = "DISPOSE", _("Dispose (final option)")


class UserDecision(models.TextChoices):
    """What a person did with an AI suggestion (Section 9.7)."""

    ACCEPTED = "ACCEPTED", _("Accepted")
    EDITED = "EDITED", _("Edited")
    REJECTED = "REJECTED", _("Rejected")
    IGNORED = "IGNORED", _("Ignored")
