"""Public interface of the Notifications module (C8, ADR-4 outbox)."""
from __future__ import annotations

from datetime import timedelta

from django.urls import NoReverseMatch, reverse
from django.utils import timezone, translation

from apps.common.errors import Forbidden

from .models import Channel, DeliveryStatus, Notification, NotificationType


class Msg:
    """A message template (gettext_lazy) and its values, rendered once per language when it is sent.

    Values may be callables (e.g. a choice label) so they are worked out inside each language."""

    def __init__(self, template, **params):
        self.template, self.params = template, params

    def render(self, lang: str) -> str:
        with translation.override(lang):
            values = {k: (v() if callable(v) else v) for k, v in self.params.items()}
            return str(self.template) % {k: str(v) for k, v in values.items()}


def enqueue(recipient, event_type: str, message, subject_ref: str = "", email: bool = False) -> None:
    """Never blocks or fails the caller's workflow. In-app messages are 'sent' immediately;
    e-mails stay PENDING until the worker delivers them. `message` is a Msg (stored in English and Arabic)
    or plain text."""
    if isinstance(message, Msg):
        en, ar = message.render("en"), message.render("ar")
    else:
        en, ar = str(message), ""
    Notification.objects.create(recipient=recipient, channel=Channel.IN_APP, event_type=event_type,
                                subject_ref=subject_ref, message=en, message_ar=ar, delivery_status=DeliveryStatus.SENT)
    if email:
        Notification.objects.create(recipient=recipient, channel=Channel.EMAIL, event_type=event_type,
                                    subject_ref=subject_ref, message=en, message_ar=ar)


def inbox(user, unread_only: bool = False):
    qs = Notification.objects.filter(recipient=user, channel=Channel.IN_APP)
    return qs.filter(read_at__isnull=True) if unread_only else qs


def unread_count(user) -> int:
    return inbox(user, unread_only=True).count()


def mark_read(user, notification_id) -> Notification:
    n = Notification.objects.get(pk=notification_id)
    if n.recipient_id != user.pk:
        raise Forbidden("Not your notification")
    if n.read_at is None:
        n.read_at = timezone.now()
        n.save(update_fields=["read_at"])
    return n


def mark_all_read(user) -> int:
    return inbox(user, unread_only=True).update(read_at=timezone.now())


def grouped(notes) -> list[tuple[str, list]]:
    """[('today', [...]), ('yesterday', [...]), ('earlier', [...])] for the page; empty groups dropped."""
    today = timezone.localdate()
    groups = {"today": [], "yesterday": [], "earlier": []}
    for n in notes:
        d = timezone.localtime(n.created_at).date()
        groups["today" if d == today else "yesterday" if d == today - timedelta(days=1) else "earlier"].append(n)
    return [(k, v) for k, v in groups.items() if v]


ICON = {
    NotificationType.REQUEST_SUBMITTED: "inbox", NotificationType.REQUEST_APPROVED: "check",
    NotificationType.REQUEST_REJECTED: "close", NotificationType.REQUEST_CANCELLED: "close",
    NotificationType.TRANSFER_DISPATCHED: "truck", NotificationType.TRANSFER_RECEIVED: "box",
    NotificationType.ASSET_REGISTERED: "plus", NotificationType.MAINTENANCE_UPDATE: "wrench",
    NotificationType.REPORT_READY: "chart", NotificationType.OTHER: "bell", NotificationType.NEED_MATCH: "search",
    NotificationType.AVAILABILITY: "bell", NotificationType.ASSET_QUESTION: "inbox", NotificationType.ASSET_ANSWER: "inbox",
}


def target_url(n: Notification, user) -> str:
    """Where a notification leads, worked out when it is opened so it follows the person's current role.
    Lazy imports: this module sits below the others and must not import them at load time."""
    kind, _, pk = (n.subject_ref or "").partition(":")
    try:
        if kind == "ResourceRequest" and pk:
            from apps.resource_requests.models import ResourceRequest
            req = ResourceRequest.objects.filter(pk=pk).only("requester_id").first()
            if req is not None and req.requester_id == user.pk:
                return reverse("resource_requests:mine") + f"?show=all#r-{pk}"
            if n.event_type == NotificationType.REQUEST_APPROVED:  # facilities: something to move
                return reverse("transfers:board")
            return reverse("transfers:queue")
        if kind == "Transfer":
            from apps.access.permissions import has_any
            return reverse("transfers:board") if has_any(user, "transfer.dispatch") else reverse("catalogue:mine")
        if kind == "Asset" and pk:
            return reverse("catalogue:panel", args=[pk])
        if kind in ("MaintenanceRecord", "EndOfLifeProposal"):
            return reverse("lifecycle:maintenance")
        if kind in ("AISummary", "Report"):
            return reverse("reporting:index")
    except NoReverseMatch:
        pass
    return reverse("notifications:index")
