"""Phase 7: questions on an asset."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogue import services as cat
from apps.catalogue.models import Asset, AssetQuestion, AssetState
from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import Notification, NotificationType

from .factories import World


class QuestionTests(TestCase):
    def setUp(self):
        self.w = World()
        self.a = self.w.asset

    def test_ask_and_answer_notify_both_sides(self):
        q = cat.ask_question(self.w.requester, self.a, "  Does this monitor have an HDMI port? ")
        self.assertEqual(q.text, "Does this monitor have an HDMI port?")
        self.assertTrue(Notification.objects.filter(recipient=self.w.custodian, event_type=NotificationType.ASSET_QUESTION).exists())
        cat.answer_question(self.w.custodian, q, "Yes, it has two HDMI ports.")
        q.refresh_from_db()
        self.assertTrue(q.is_answered)
        n = Notification.objects.get(recipient=self.w.requester, event_type=NotificationType.ASSET_ANSWER, channel="IN_APP")
        self.assertEqual(n.subject_ref, f"Asset:{self.a.pk}")
        self.assertTrue(n.message_ar)

    def test_validation(self):
        for bad in ("", "  ", "ab", "x" * 501):
            with self.assertRaises(ValidationFailed):
                cat.ask_question(self.w.requester, self.a, bad)
        q = cat.ask_question(self.w.requester, self.a, "Is the stand included?")
        for bad in ("", "x" * 1001):
            with self.assertRaises(ValidationFailed):
                cat.answer_question(self.w.custodian, q, bad)

    def test_who_may_ask_and_answer(self):
        with self.assertRaises(ValidationFailed):  # the custodian answers, doesn't ask
            cat.ask_question(self.w.custodian, self.a, "Who owns this?")
        q = cat.ask_question(self.w.requester, self.a, "Is the stand included?")
        for outsider in (self.w.requester2, self.w.approver):
            with self.assertRaises(Forbidden):
                cat.answer_question(outsider, q, "Sure")
        cat.unpublish(self.w.custodian, self.a)
        with self.assertRaises(Forbidden):  # can't see it any more, so can't ask about it
            cat.ask_question(self.w.requester2, self.a, "Still there?")

    def test_spam_guard(self):
        for i in range(3):
            cat.ask_question(self.w.requester, self.a, f"Question number {i}?")
        with self.assertRaises(ValidationFailed):
            cat.ask_question(self.w.requester, self.a, "One more?")

    def test_archived_items_take_no_questions_and_close_open_ones(self):
        q = cat.ask_question(self.w.requester, self.a, "Is the stand included?")
        Asset.objects.filter(pk=self.a.pk).update(lifecycle_state=AssetState.RECYCLED, publication_status="UNPUBLISHED")
        q.refresh_from_db()
        self.assertTrue(q.is_closed)
        with self.assertRaises(ValidationFailed):
            cat.answer_question(self.w.custodian, q, "Too late")
        self.assertNotIn(q, cat.questions_to_answer(self.w.custodian))

    def test_withdraw_only_own_unanswered(self):
        q = cat.ask_question(self.w.requester, self.a, "Is the stand included?")
        with self.assertRaises(Forbidden):
            cat.withdraw_question(self.w.requester2, q)
        cat.withdraw_question(self.w.requester, q)
        self.assertFalse(AssetQuestion.objects.exists())

    def test_unanswered_list_and_badge(self):
        cat.ask_question(self.w.requester, self.a, "Is the stand included?")
        self.assertEqual(cat.unanswered_count(self.w.custodian), 1)
        self.assertEqual(cat.unanswered_count(self.w.requester), 0)


class QuestionScreenTests(TestCase):
    def setUp(self):
        self.w = World()
        self.a = self.w.asset

    def test_others_see_the_unit_not_the_name(self):
        cat.ask_question(self.w.requester, self.a, "Does it have HDMI?")
        self.client.force_login(self.w.requester2)
        r = self.client.get(reverse("catalogue:panel", args=[self.a.pk]))
        self.assertContains(r, "Does it have HDMI?")
        self.assertContains(r, "Asked by someone in ME")
        self.assertNotContains(r, self.w.requester.full_name + " (")
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("catalogue:panel", args=[self.a.pk]))
        self.assertContains(r, "Rana (ME)")
        self.assertContains(r, "Post answer")

    def test_ask_answer_through_the_panel(self):
        self.client.force_login(self.w.requester)
        r = self.client.post(reverse("catalogue:ask", args=[self.a.pk]), {"text": "Is it VESA mountable?"}, HTTP_HX_REQUEST="true")
        self.assertContains(r, "Is it VESA mountable?")
        r = self.client.post(reverse("catalogue:ask", args=[self.a.pk]), {"text": ""}, HTTP_HX_REQUEST="true")
        self.assertContains(r, "at least 3 characters")
        q = AssetQuestion.objects.get()
        self.assertEqual(self.client.post(reverse("catalogue:answer", args=[q.pk]), {"text": "No"}).status_code, 404)
        self.client.force_login(self.w.custodian)
        r = self.client.post(reverse("catalogue:answer", args=[q.pk]), {"text": "Yes, 100 mm."}, HTTP_HX_REQUEST="true")
        self.assertContains(r, "Yes, 100 mm.")
        mine = self.client.get(reverse("catalogue:mine"))
        self.assertNotContains(mine, "waiting for your answer")

    def test_questions_page(self):
        q = cat.ask_question(self.w.requester, self.a, "Is it VESA mountable?")
        AssetQuestion.objects.filter(pk=q.pk).update(asked_at=timezone.now() - timedelta(days=20))
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("catalogue:questions"))
        self.assertContains(r, "Waiting for your answer")
        self.assertContains(r, "Waiting 20 days")
        self.assertContains(self.client.get(reverse("catalogue:mine")), "1 question is waiting for your answer.")
        self.client.force_login(self.w.requester)
        self.assertContains(self.client.get(reverse("catalogue:questions")), "Is it VESA mountable?")
