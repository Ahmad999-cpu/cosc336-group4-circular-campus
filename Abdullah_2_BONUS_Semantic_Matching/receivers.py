"""Listens to the Requests module (see apps/resource_requests/signals.py)."""
from django.dispatch import receiver

from apps.resource_requests.signals import request_sent

from . import services


@receiver(request_sent)
def count_suggestion_as_accepted(sender, request, by, match_ref="", **kwargs):
    if match_ref:
        services.note_request_from_match(match_ref, by)


# Phase 5: an item was published or got free units again -> check saved needs after the transaction commits,
# so a slow or failing check can never undo or delay the custodian's own action.
from django.db import transaction  # noqa: E402

from apps.catalogue.signals import asset_history  # noqa: E402

TRIGGERS = {"PUBLICATION", "ALLOCATION", "STATE_CHANGE", "UPDATE", "CONDITION_UPDATE"}


@receiver(asset_history, dispatch_uid="matching.saved_needs")
def check_saved_needs(sender, asset, event_type="", description="", availability=None, **kwargs):
    if availability is not None:  # Phase 6: expected date changed or cancelled
        from .wishlist import availability_changed
        kind, before, after = availability
        pk = asset.pk
        transaction.on_commit(lambda: availability_changed(type(asset).objects.get(pk=pk), kind, before, after))
    if event_type not in TRIGGERS or asset.publication_status != "PUBLISHED" or asset.unreserved_quantity <= 0:
        return
    if event_type == "ALLOCATION" and "released" not in description:
        return  # a reservation takes units away; only a release can create a new match
    pk = asset.pk
    transaction.on_commit(lambda: _safe_check(pk))


def _safe_check(pk):
    from apps.catalogue.models import Asset

    from .wishlist import check_asset
    try:
        check_asset(Asset.objects.get(pk=pk))
    except Exception as exc:  # never surfaces to the person who published
        import logging
        logging.getLogger(__name__).warning("saved-need check failed: %s", exc)
