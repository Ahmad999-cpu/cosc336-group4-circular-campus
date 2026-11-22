"""Background worker (ADR-1, ADR-4): delivers the e-mail outbox and computes embeddings.

Run it next to the web server:  python manage.py runworker
A simple polling loop on purpose: no Redis or Celery to install for a prototype of ~200 users.
"""
import time

from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.matching.services import embed_pending
from apps.notifications.models import Channel, DeliveryStatus, Notification


def deliver_outbox(limit: int = 50) -> int:
    sent = 0
    for n in Notification.objects.filter(channel=Channel.EMAIL, delivery_status=DeliveryStatus.PENDING).select_related("recipient")[:limit]:
        try:
            send_mail(subject=n.get_event_type_display(), message=n.message, from_email=None,
                      recipient_list=[n.recipient.email])
            n.mark_sent()
            sent += 1
        except Exception as exc:  # recorded and shown to the actor; never retried silently forever
            n.mark_failed(str(exc)[:500])
    return sent


class Command(BaseCommand):
    help = "Deliver queued e-mails and compute embeddings, forever (Ctrl+C to stop)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one cycle and exit (useful in tests)")
        parser.add_argument("--interval", type=float, default=5.0)

    def handle(self, *args, once=False, interval=5.0, **opts):
        while True:
            mails = deliver_outbox()
            vectors = embed_pending()
            if mails or vectors:
                self.stdout.write(f"delivered {mails} e-mail(s), embedded {vectors} item(s)")
            if once:
                return
            time.sleep(interval)
