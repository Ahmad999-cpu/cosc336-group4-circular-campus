"""Domain signal sent after a request is created.

The Matching module listens so a suggestion that led to a request is counted as accepted (AI feedback,
Section 9.7) without this module importing Matching (calls go down only).
"""
from django.dispatch import Signal

# kwargs: request, by, match_ref (the MatchRecommendation id the person came from, or "")
request_sent = Signal()
