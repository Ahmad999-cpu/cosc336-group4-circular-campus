"""Feature 1: QR labels. The code holds only the address; opening it goes through sign-in and can_view."""
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalogue import qr, services
from apps.catalogue.models import Asset, AssetState
from apps.common.errors import Forbidden, ValidationFailed

from .factories import World, role, user


class QrServiceTests(TestCase):
    def setUp(self):
        self.w = World()

    @override_settings(SITE_BASE_URL="https://cc.example.edu")
    def test_url_uses_the_configured_base_and_only_the_id(self):
        url = qr.asset_url(self.w.asset)
        self.assertEqual(url, f"https://cc.example.edu/assets/{self.w.asset.pk}/")
        self.assertNotIn("Dell", url)
        self.assertNotIn("650", url)

    @override_settings(SITE_BASE_URL="", ALLOWED_HOSTS=["10.0.0.5"])
    def test_without_a_base_url_it_uses_the_request_host_never_a_fixed_one(self):
        from django.test import RequestFactory
        req = RequestFactory().get("/", HTTP_HOST="10.0.0.5:8000")
        self.assertEqual(qr.asset_url(self.w.asset, req), f"http://10.0.0.5:8000/assets/{self.w.asset.pk}/")
        with self.assertRaises(ValueError):
            qr.asset_url(self.w.asset)

    def test_label_names_the_asset_and_holds_a_code(self):
        svg = qr.label_svg(self.w.asset, "https://x.test/assets/1/", scan_hint="Scan", id_label="Asset ID")
        self.assertIn("Dell monitor", svg)
        self.assertIn(qr.short_id(self.w.asset), svg)
        self.assertIn("<path", svg)

    def test_label_escapes_names(self):
        self.w.asset.name = "<script>x</script>"
        svg = qr.label_svg(self.w.asset, "https://x.test/a/", scan_hint="Scan", id_label="ID")
        self.assertNotIn("<script>", svg)

    def test_who_may_label(self):
        self.assertTrue(services.can_label(self.w.custodian, self.w.asset))
        self.assertFalse(services.can_label(self.w.requester, self.w.asset))
        self.assertFalse(services.can_label(self.w.approver, self.w.asset))
        tech = user("Tariq", self.w.uni, (role("Maintenance", "maintenance.record"), None))
        self.assertTrue(services.can_label(tech, self.w.asset))
        with self.assertRaises(Forbidden):
            services.require_label(self.w.requester, self.w.asset)

    def test_no_new_label_once_the_asset_has_left_the_register(self):
        Asset.objects.filter(pk=self.w.asset.pk).update(lifecycle_state=AssetState.DISPOSED)
        self.w.asset.refresh_from_db()
        with self.assertRaises(ValidationFailed):
            services.require_label(self.w.custodian, self.w.asset)


@override_settings(SITE_BASE_URL="https://cc.example.edu")
class QrScreenTests(TestCase):
    def setUp(self):
        self.w = World()

    def test_scanning_while_signed_out_goes_to_sign_in_and_back(self):
        url = reverse("catalogue:panel", args=[self.w.asset.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("access:login"), r["Location"])
        self.assertIn("next=", r["Location"])

    def test_scanned_page_shows_what_the_user_may_see(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk]))
        self.assertContains(r, "Dell monitor")
        self.assertContains(r, "Request this")
        self.assertNotContains(r, "QR label")  # requesters scan; they don't print labels

    def test_unpublished_asset_is_hidden_from_people_outside_the_unit(self):
        services.unpublish(self.w.custodian, self.w.asset)
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "available to you", status_code=404)

    def test_unknown_asset_gets_the_same_answer(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("catalogue:panel", args=[uuid.uuid4()]))
        self.assertEqual(r.status_code, 404)

    def test_custodian_sees_and_downloads_the_label(self):
        self.client.force_login(self.w.custodian)
        page = self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk]))
        self.assertContains(page, reverse("catalogue:qr", args=[self.w.asset.pk]))
        r = self.client.get(reverse("catalogue:qr", args=[self.w.asset.pk]))
        self.assertContains(r, "Print label")
        self.assertContains(r, f"https://cc.example.edu/assets/{self.w.asset.pk}/")
        d = self.client.get(reverse("catalogue:qr_download", args=[self.w.asset.pk]))
        self.assertEqual(d["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertIn("attachment;", d["Content-Disposition"])
        self.assertIn(b"Dell monitor", d.content)

    def test_others_cannot_open_the_label_pages(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("catalogue:qr", args=[self.w.asset.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("catalogue:qr_download", args=[self.w.asset.pk])).status_code, 404)

    def test_removed_asset_page_explains_and_offers_no_label(self):
        services.unpublish(self.w.custodian, self.w.asset)
        Asset.objects.filter(pk=self.w.asset.pk).update(lifecycle_state=AssetState.RECYCLED)
        self.client.force_login(self.w.custodian)
        r = self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk]))
        self.assertContains(r, "No longer in service")
        self.assertNotContains(r, reverse("catalogue:qr", args=[self.w.asset.pk]))
        label = self.client.get(reverse("catalogue:qr", args=[self.w.asset.pk]))
        self.assertContains(label, "No label for this item")
        self.assertEqual(self.client.get(reverse("catalogue:qr_download", args=[self.w.asset.pk])).status_code, 404)

    @override_settings(DEBUG=True)
    def test_demo_sign_in_never_follows_an_outside_next(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("seed_demo", stdout=StringIO())
        r = self.client.post(reverse("access:demo_login"), {"email": "club@demo.local", "next": "https://evil.example/"})
        self.assertFalse(r["Location"].startswith("https://evil"))
        r = self.client.post(reverse("access:demo_login"), {"email": "club@demo.local", "next": "/assets/"})
        self.assertEqual(r["Location"], "/assets/")

