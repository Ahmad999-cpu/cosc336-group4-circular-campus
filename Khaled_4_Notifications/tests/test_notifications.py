"""C8: every key event notifies the right people; the inbox, mark read, links, badges; e-mail never blocks work."""
import uuid
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.notifications import services
from apps.notifications.models import Channel, DeliveryStatus, Notification, NotificationType
from apps.resource_requests import services as req_services
from apps.transfers import services as tr

from .factories import World


def types_for(u):
    return set(Notification.objects.filter(recipient=u, channel=Channel.IN_APP).values_list("event_type", flat=True))


class C8EventTests(TestCase):
    """Lab slide C8: messages when a request is made, approved, rejected or received."""

    def setUp(self):
        self.w = World(qty=3)

    def send(self, who=None, qty=1):
        r, _ = req_services.submit_request(who or self.w.requester, {
            "department": self.w.me, "selected_asset": self.w.asset, "quantity": qty, "purpose": "Lab",
            "destination_campus": "Main"}, uuid.uuid4().hex)
        return r

    def test_made_approved_received(self):
        r = self.send()
        self.assertIn(NotificationType.REQUEST_SUBMITTED, types_for(self.w.requester))
        self.assertIn(NotificationType.REQUEST_SUBMITTED, types_for(self.w.approver))
        tr.approve_request(r.pk, self.w.approver)
        self.assertIn(NotificationType.REQUEST_APPROVED, types_for(self.w.requester))
        t = tr.transfer_for_request(r)
        tr.dispatch(t.pk, self.w.facilities, "Van")
        self.assertIn(NotificationType.TRANSFER_DISPATCHED, types_for(self.w.requester))
        tr.confirm_receipt(t.pk, self.w.requester, 1)
        self.assertIn(NotificationType.TRANSFER_RECEIVED, types_for(self.w.custodian))

    def test_rejected(self):
        r = self.send()
        tr.reject_request(r.pk, self.w.approver, "Not this term")
        n = Notification.objects.get(recipient=self.w.requester, event_type=NotificationType.REQUEST_REJECTED, channel=Channel.IN_APP)
        self.assertIn("Not this term", n.message)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="mail.invalid", EMAIL_PORT=1)
    def test_broken_email_never_blocks_and_is_recorded(self):
        r = self.send()
        tr.approve_request(r.pk, self.w.approver)
        t = tr.transfer_for_request(r)
        tr.dispatch(t.pk, self.w.facilities, "Van")  # queues an e-mail
        emails = Notification.objects.filter(channel=Channel.EMAIL)
        self.assertTrue(emails.exists())
        self.assertFalse(emails.exclude(delivery_status=DeliveryStatus.PENDING).exists())
        call_command("runworker", once=True, stdout=mock.MagicMock())
        self.assertFalse(emails.exclude(delivery_status=DeliveryStatus.FAILED).exists())
        self.assertFalse(emails.filter(failure_reason="").exists())


class InboxTests(TestCase):
    def setUp(self):
        self.w = World(qty=3)
        self.r, _ = req_services.submit_request(self.w.requester, {
            "department": self.w.me, "selected_asset": self.w.asset, "quantity": 1, "purpose": "Lab",
            "destination_campus": "Main"}, uuid.uuid4().hex)

    def test_links_follow_the_reader(self):
        mine = Notification.objects.get(recipient=self.w.requester, channel=Channel.IN_APP)
        theirs = Notification.objects.get(recipient=self.w.approver, channel=Channel.IN_APP)
        self.assertIn(reverse("resource_requests:mine"), services.target_url(mine, self.w.requester))
        self.assertEqual(services.target_url(theirs, self.w.approver), reverse("transfers:queue"))
        odd = Notification(recipient=self.w.requester, event_type=NotificationType.OTHER, subject_ref="Nothing:1", message="x")
        self.assertEqual(services.target_url(odd, self.w.requester), reverse("notifications:index"))

    def test_open_marks_read_and_redirects(self):
        self.client.force_login(self.w.approver)
        n = Notification.objects.get(recipient=self.w.approver, channel=Channel.IN_APP)
        r = self.client.get(reverse("notifications:open", args=[n.pk]))
        self.assertRedirects(r, reverse("transfers:queue"), fetch_redirect_response=False)
        n.refresh_from_db()
        self.assertIsNotNone(n.read_at)

    def test_someone_elses_notification_is_refused(self):
        self.client.force_login(self.w.requester2)
        n = Notification.objects.get(recipient=self.w.approver, channel=Channel.IN_APP)
        self.assertEqual(self.client.get(reverse("notifications:open", args=[n.pk])).status_code, 403)

    def test_page_tabs_and_mark_all(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("notifications:index"))
        self.assertContains(r, "Today")
        self.assertContains(r, "Mark all as read")
        self.client.post(reverse("notifications:read_all"), {"next": "/notifications/"})
        self.assertEqual(services.unread_count(self.w.requester), 0)
        r = self.client.get(reverse("notifications:index"), {"show": "unread"})
        self.assertContains(r, "You're all caught up")
        r = self.client.post(reverse("notifications:read_all"), {"next": "https://evil.example/"})
        self.assertEqual(r["Location"], "/")  # no open redirect

    def test_badges_endpoint(self):
        self.client.force_login(self.w.approver)
        d = self.client.get(reverse("web:badges")).json()
        self.assertEqual(d["unread"], 1)
        self.assertGreaterEqual(d["nav"].get("approvals", 0), 1)

    def test_actions_ask_the_page_to_refresh_badges(self):
        from apps.web.htmx import with_toast
        from django.http import HttpResponse
        self.assertIn("cc:refresh", with_toast(HttpResponse(), "Done")["HX-Trigger-After-Settle"])
