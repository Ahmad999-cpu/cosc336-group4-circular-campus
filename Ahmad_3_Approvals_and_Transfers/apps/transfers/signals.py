"""Domain signal sent after a receiver confirms a transfer.

The Sustainability module listens and records the impact (avoided purchase, carbon, waste) without this
module importing Sustainability (Sustainability already depends on Transfer).
"""
from django.dispatch import Signal

# kwargs: transfer, quantity, by
transfer_received = Signal()
