"""Keeps a UserSession row per logged-in browser session and enforces the 15-minute idle limit (NFR-17).

Django's SESSION_COOKIE_AGE already expires idle cookies; this row adds the audit trail the design asks for.
"""
from django.contrib.auth import logout
from django.utils import timezone

from .models import SESSION_IDLE_LIMIT, SessionStatus, UserSession


def is_background(request) -> bool:
    """Automatic refreshes (badge counts, the approvals queue) are not activity: they must not keep an idle
    session alive (found in validation: the one-minute badge refresh defeated the 15-minute limit)."""
    return request.headers.get("X-Background") == "1"


class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and request.session.session_key:
            if not is_background(request):
                request.session.modified = True  # renews the 15-minute cookie (SESSION_SAVE_EVERY_REQUEST is off)
            now = timezone.now()
            key = request.session.session_key
            row = UserSession.objects.filter(user=user, session_key=key, status=SessionStatus.ACTIVE).first()
            if row is None:
                UserSession.objects.create(user=user, session_key=key, expires_at=now + SESSION_IDLE_LIMIT)
            elif row.is_expired(now):
                row.status = SessionStatus.EXPIRED
                row.save(update_fields=["status"])
                logout(request)
            elif not is_background(request):
                row.touch(now)
        return self.get_response(request)
