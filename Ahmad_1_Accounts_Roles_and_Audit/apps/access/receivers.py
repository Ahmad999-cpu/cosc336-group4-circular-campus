"""Audit sign-ins, sign-outs and failed attempts (NFR-18)."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in, dispatch_uid="access.audit_login")
def audit_login(sender, request, user, **kwargs):
    from apps.audit.services import record
    record(user, "sign_in", "User", user.pk)


@receiver(user_logged_out, dispatch_uid="access.audit_logout")
def audit_logout(sender, request, user, **kwargs):
    if user is not None:
        from apps.audit.services import record
        record(user, "sign_out", "User", user.pk)


@receiver(user_login_failed, dispatch_uid="access.audit_failed")
def audit_failed(sender, credentials, request=None, **kwargs):
    from apps.audit.services import record
    record(None, "sign_in_failed", "User", None, after={"email": str(credentials.get("username", ""))[:120]}, outcome="FAILED")
