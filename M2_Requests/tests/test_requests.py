import uuid
from datetime import date, timedelta

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.common.errors import Forbidden, ValidationFailed
from apps.notifications.models import Notification
from apps.resource_requests import services
from apps.resource_requests.models import RequestStatus, ResourceRequest

from .factories import World


def form(w, **kw):
    d = {"department": w.me, "selected_asset": w.asset, "quantity": 1, "purpose": "Club workstation", "specifications": "",
         "preferred_condition": "ANY", "urgency": "MEDIUM", "required_date": date.today() + timedelta(days=7),
         "destination_campus": "Main", "destination_building": "B2", "destination_room": "1.30"}
    d.update(kw)
    return d


class SubmitTests(TestCase):
    def setUp(self):
        self.w = World(qty=3)

    def test_submit_creates_pending_and_notifies(self):
        req, created = services.submit_request(self.w.requester, form(self.w), uuid.uuid4().hex)
        self.assertTrue(created)
        self.assertEqual(req.status, RequestStatus.PENDING_APPROVAL)
        self.assertEqual(req.category, self.w.category)
        self.assertTrue(Notification.objects.filter(recipient=self.w.requester).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.w.approver).exists())

    def test_same_key_returns_the_first_request(self):
        key = uuid.uuid4().hex
        a, _ = services.submit_request(self.w.requester, form(self.w), key)
        b, created = services.submit_request(self.w.requester, form(self.w), key)
        self.assertEqual((a.pk, created), (b.pk, False))
        self.assertEqual(ResourceRequest.objects.count(), 1)

    def test_rules(self):
        with self.assertRaises(ValidationFailed):  # more than free
            services.submit_request(self.w.requester, form(self.w, quantity=4), uuid.uuid4().hex)
        with self.assertRaises(Forbidden):  # no request.submit for that unit
            services.submit_request(self.w.requester, form(self.w, department=self.w.cs), uuid.uuid4().hex)
        with self.assertRaises(ValidationFailed):  # past date (model rule)
            services.submit_request(self.w.requester, form(self.w, required_date=date.today() - timedelta(days=1)), uuid.uuid4().hex)
        with self.assertRaises(ValidationFailed):  # no category and no asset
            services.submit_request(self.w.requester, form(self.w, selected_asset=None), uuid.uuid4().hex)

    def test_request_without_an_item(self):
        req, _ = services.submit_request(self.w.requester, form(self.w, selected_asset=None, category=self.w.category), uuid.uuid4().hex)
        self.assertIsNone(req.selected_asset)


class ChangeTests(TestCase):
    def setUp(self):
        self.w = World(qty=3)
        self.req, _ = services.submit_request(self.w.requester, form(self.w), uuid.uuid4().hex)

    def test_edit_and_cancel_by_owner_only(self):
        with self.assertRaises(Forbidden):
            services.edit_request(self.w.requester2, self.req, {"quantity": 2})
        services.edit_request(self.w.requester, self.req, {"quantity": 2})
        self.req.refresh_from_db()
        self.assertEqual(self.req.quantity, 2)
        with self.assertRaises(ValidationFailed):
            services.cancel_request(self.w.requester, self.req, "  ")
        services.cancel_request(self.w.requester, self.req, "Found one in our store")
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, RequestStatus.CANCELLED)
        with self.assertRaises(ValidationFailed):
            services.edit_request(self.w.requester, self.req, {"quantity": 1})

    def test_progress(self):
        self.assertEqual(services.progress_index(self.req), 0)


@override_settings(ALLOWED_HOSTS=["testserver"])
class ScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=3)
        self.client.force_login(self.w.requester)

    def test_new_from_an_item_and_my_requests(self):
        r = self.client.get(reverse("resource_requests:new"), {"asset": self.w.asset.pk})
        self.assertContains(r, "Dell monitor")
        key = r.context["form"].initial["idempotency_key"]
        post = {"asset": self.w.asset.pk, "department": self.w.me.pk, "quantity": 2, "purpose": "Club", "preferred_condition": "ANY",
                "urgency": "MEDIUM", "destination_campus": "Main", "idempotency_key": key}
        r = self.client.post(reverse("resource_requests:new"), post)
        self.assertEqual(r.status_code, 302)
        self.client.post(reverse("resource_requests:new"), post)  # double submit
        self.assertEqual(ResourceRequest.objects.count(), 1)
        r = self.client.get(reverse("resource_requests:mine"))
        self.assertContains(r, "2 × Dell monitor")

    def test_too_many_units_shows_a_field_error(self):
        r = self.client.get(reverse("resource_requests:new"), {"asset": self.w.asset.pk})
        post = {"asset": self.w.asset.pk, "department": self.w.me.pk, "quantity": 9, "purpose": "Club", "preferred_condition": "ANY",
                "urgency": "MEDIUM", "destination_campus": "Main", "idempotency_key": "k1"}
        r = self.client.post(reverse("resource_requests:new"), post)
        self.assertContains(r, "Only 3 free")

    def test_others_cannot_see_my_request(self):
        req, _ = services.submit_request(self.w.requester, form(self.w), uuid.uuid4().hex)
        self.client.force_login(self.w.requester2)
        self.assertEqual(self.client.get(reverse("resource_requests:detail", args=[req.pk])).status_code, 404)

    def test_cancel_over_htmx(self):
        req, _ = services.submit_request(self.w.requester, form(self.w), uuid.uuid4().hex)
        r = self.client.post(reverse("resource_requests:cancel", args=[req.pk]), {"reason": "No longer needed"}, HTTP_HX_REQUEST="true")
        self.assertEqual(r["HX-Redirect"], reverse("resource_requests:mine"))
