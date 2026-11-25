"""Public interface of the Audit module."""
from .models import AuditLog


def record(actor, action: str, entity_type: str = "", entity_id=None, before=None, after=None, outcome: str = "SUCCESS") -> None:
    AuditLog.objects.create(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id,
                            before_value=before, after_value=after, outcome=outcome)
