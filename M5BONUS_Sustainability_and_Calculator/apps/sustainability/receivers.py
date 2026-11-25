"""Listens to the Transfers module (see apps/transfers/signals.py)."""
from django.dispatch import receiver

from apps.transfers.signals import transfer_received

from . import services


@receiver(transfer_received)
def record_impact(sender, transfer, quantity, by, **kwargs):
    services.record_transfer_impact(transfer, quantity)
