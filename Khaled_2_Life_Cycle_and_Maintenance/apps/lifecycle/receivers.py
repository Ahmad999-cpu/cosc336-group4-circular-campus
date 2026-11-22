"""Writes a LifeCycleEvent for every Asset operation (listens to catalogue.signals.asset_history)."""
from django.dispatch import receiver

from apps.catalogue.models import Asset
from apps.catalogue.signals import asset_history

from .models import EventType, LifeCycleEvent

_VALID_TYPES = {c.value for c in EventType}


@receiver(asset_history, sender=Asset, dispatch_uid="lifecycle.record_asset_history")
def record_asset_history(sender, asset, previous_state, new_state, by, event_type, description="",
                         approval_ref=None, source=None, **kwargs):
    if event_type == "STATE_CHANGE" and approval_ref is not None:
        event_type = EventType.END_OF_LIFE
    LifeCycleEvent.objects.create(
        asset=asset, recorded_by=by,
        event_type=event_type if event_type in _VALID_TYPES else EventType.STATE_CHANGE,
        description=description, previous_state=previous_state or "", new_state=new_state or "",
        approval_ref=approval_ref,
        source_type=type(source).__name__ if source is not None else "",
        source_id=getattr(source, "pk", None),
    )
