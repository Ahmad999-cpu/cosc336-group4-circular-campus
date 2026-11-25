"""Contact form delivery. Messages are always saved; e-mail is sent through Django's configured backend.

Honesty rule: the visitor is only told "sent" when a real mail backend accepted the message. With the
console or memory backend (development) or no SMTP host, the message is saved and the page says so.
"""
from __future__ import annotations

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage

from .models import ContactMessage, DeliveryStatus

log = logging.getLogger(__name__)
REAL_BACKENDS = ("django.core.mail.backends.smtp.EmailBackend",)


def delivery_configured() -> bool:
    """True only for a real backend: SMTP with a host, or a backend set up explicitly for a mail service."""
    backend = settings.EMAIL_BACKEND
    if backend in REAL_BACKENDS:
        return bool(settings.EMAIL_HOST)
    return backend not in ("django.core.mail.backends.console.EmailBackend", "django.core.mail.backends.locmem.EmailBackend",
                           "django.core.mail.backends.dummy.EmailBackend", "django.core.mail.backends.filebased.EmailBackend")


def visitor_key(ip: str) -> str:
    return hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()


def rate_limited(key: str) -> bool:
    """At most CONTACT_RATE_LIMIT messages per hour per visitor address (cache counter)."""
    ck = f"guest-contact:{key}"
    n = cache.get(ck, 0)
    if n >= settings.CONTACT_RATE_LIMIT:
        return True
    cache.set(ck, n + 1, 3600)
    return False


def deliver(data: dict, *, ip_key: str = "", language: str = "") -> ContactMessage:
    msg = ContactMessage(name=data["name"], email=data["email"], organisation=data["organisation"], phone=data.get("phone", ""),
                         message=data["message"], language=language[:8], ip_hash=ip_key)
    if not delivery_configured():
        msg.delivery = DeliveryStatus.NOT_CONFIGURED
        if settings.DEBUG:  # development: still show it in the console so it can be checked
            _email(msg).send(fail_silently=True)
        msg.save()
        return msg
    try:
        _email(msg).send(fail_silently=False)
        msg.delivery = DeliveryStatus.SENT
    except Exception as exc:  # SMTP down, bad credentials, timeout: keep the message, report honestly
        log.warning("Contact e-mail failed: %s", exc)
        msg.delivery, msg.delivery_error = DeliveryStatus.FAILED, str(exc)[:300]
    msg.save()
    return msg


def _email(m: ContactMessage) -> EmailMessage:
    body = (f"New message from the {settings.BRAND_NAME} contact form\n\n"
            f"Name: {m.name}\nE-mail: {m.email}\nOrganisation: {m.organisation}\nPhone: {m.phone or '-'}\n"
            f"Language: {m.language or '-'}\n\n{m.message}\n")
    subject = f"[{settings.BRAND_NAME}] Contact form: {m.organisation}"[:150].replace("\n", " ")
    return EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_RECIPIENT], reply_to=[m.email])
