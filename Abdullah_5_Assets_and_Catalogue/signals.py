"""Domain signal sent by Asset operations.

The Life Cycle module listens and writes a LifeCycleEvent inside the same database transaction
(Django signals run synchronously), so history can never be skipped and Catalogue never imports
Life Cycle (component diagram rule: calls go down only).
"""
from django.dispatch import Signal

# kwargs: asset, previous_state, new_state, by, event_type, description, approval_ref=None, source=None
asset_history = Signal()
