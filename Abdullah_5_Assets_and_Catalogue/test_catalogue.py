from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalogue import services
from apps.catalogue.models import AssetState, PublicationStatus
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed
from apps.lifecycle.models import LifeCycleEvent

from .factories import World, user

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82")


def data(w, **kw):
    d = {"name": "Lab stool", "category": w.category, "owner_department": w.cs, "quantity": 3, "condition": Condition.GOOD,
         "location_campus": "Main", "location_building": "B1", "location_room": "1.1", "purchase_date": date(2022, 1, 1),
         "estimated_value": Decimal("180"), "description": "", "specifications": "", "serial_number": ""}
    d.update(kw)
    return d


class RegisterAndPublishTests(TestCase):
    def setUp(self):
        self.w = World()

    def test_register_starts_registered_and_writes_history(self):
        a = services.register_asset(self.w.custodian, data(self.w), tags="stool, lab, Stool")
        self.assertEqual((a.lifecycle_state, a.publication_status), (AssetState.REGISTERED, PublicationStatus.UNPUBLISHED))
        self.assertEqual(sorted(a.tags.values_list("tag_text", flat=True)), ["lab", "stool"])
        self.assertTrue(LifeCycleEvent.objects.filter(asset=a, event_type="REGISTRATION").exists())

    def test_only_custodians_of_the_unit_register(self):
        with self.assertRaises(Forbidden):
            services.register_asset(self.w.requester, data(self.w))
        with self.assertRaises(Forbidden):  # custodian of CS cannot register for ME
            services.register_asset(self.w.custodian, data(self.w, owner_department=self.w.me))

    def test_scope_covers_child_units(self):
        college = user("Col", self.w.eng, (self.w.r_cus, self.w.eng))
        a = services.register_asset(college, data(self.w, owner_department=self.w.me))
        self.assertEqual(a.owner_department, self.w.me)

    def test_publish_needs_condition_check_first(self):
        a = services.register_asset(self.w.custodian, data(self.w))
        with self.assertRaises(ValidationFailed):
            services.publish(self.w.custodian, a)
        services.confirm_condition(self.w.custodian, a, Condition.FAIR)
        a = services.publish(self.w.custodian, a)
        self.assertEqual(a.publication_status, PublicationStatus.PUBLISHED)
        self.assertIn(a, services.published())

    def test_bad_values_refused(self):
        with self.assertRaises(ValidationFailed):
            services.register_asset(self.w.custodian, data(self.w, quantity=0))
        with self.assertRaises(ValidationFailed):
            services.register_asset(self.w.custodian, data(self.w, purchase_date=date.today() + timedelta(days=3)))

    def test_photo_upload_and_type_check(self):
        img = SimpleUploadedFile("p.png", PNG, content_type="image/png")
        a = services.register_asset(self.w.custodian, data(self.w), uploads=[img])
        self.assertIsNotNone(a.photo)
        bad = SimpleUploadedFile("x.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(ValidationFailed):
            services.update_asset(self.w.custodian, a, {}, uploads=[bad])

    def test_edit_changes_descriptive_fields_only(self):
        a = services.register_asset(self.w.custodian, data(self.w))
        services.update_asset(self.w.custodian, a, {"name": "Tall lab stool", "location_room": "2.2"})
        a.refresh_from_db()
        self.assertEqual((a.name, a.location_room), ("Tall lab stool", "2.2"))
        with self.assertRaises(ValidationFailed):
            services.update_asset(self.w.custodian, a, {"lifecycle_state": AssetState.DISPOSED})

    def test_quantity_cannot_drop_below_reserved(self):
        a = self.w.asset  # 1 unit, published in the World
        a.allocate(1, self.w.approver)
        with self.assertRaises(ValidationFailed):
            services.change_quantity(self.w.custodian, a, 0)


class SearchTests(TestCase):
    def setUp(self):
        self.w = World(qty=4)

    def test_keyword_tag_and_filters(self):
        a = services.register_asset(self.w.custodian, data(self.w, name="Ergonomic chair"), tags="seating")
        services.confirm_condition(self.w.custodian, a, Condition.GOOD)
        services.publish(self.w.custodian, a)
        self.assertEqual(list(services.search(q="seating")), [a])
        self.assertEqual(list(services.search(q="DELL")), [self.w.asset])
        self.assertEqual(len(services.search(campus="Main")), 2)
        self.assertEqual(len(services.search(condition=Condition.FAIR)), 0)
        self.assertEqual(len(services.search(department=self.w.eng)), 2)

    def test_unpublished_and_fully_reserved_are_hidden(self):
        self.w.asset.allocate(4, self.w.approver)
        self.assertEqual(len(services.search()), 0)


@override_settings(ALLOWED_HOSTS=["testserver"])
class ScreenTests(TestCase):
    def setUp(self):
        self.w = World(qty=2)

    def test_browse_and_panel(self):
        self.client.force_login(self.w.requester)
        r = self.client.get(reverse("catalogue:browse"), {"q": "dell"})
        self.assertContains(r, "Dell monitor")
        r = self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk]), HTTP_HX_REQUEST="true")
        self.assertContains(r, "drawer-title")

    def test_unpublished_asset_hidden_from_others(self):
        services.unpublish(self.w.custodian, self.w.asset)
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("catalogue:panel", args=[self.w.asset.pk])).status_code, 404)

    def test_console_is_for_custodians(self):
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("catalogue:mine")).status_code, 403)
        self.client.force_login(self.w.custodian)
        self.assertContains(self.client.get(reverse("catalogue:mine")), "Dell monitor")

    def test_register_through_the_panel(self):
        self.client.force_login(self.w.custodian)
        post = {"name": "Projector", "category": self.w.category.pk, "owner_department": self.w.cs.pk, "quantity": 2,
                "condition": "GOOD", "location_campus": "Main", "estimated_value": "1200", "tags": "projector, HDMI"}
        r = self.client.post(reverse("catalogue:new"), post, HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["HX-Retarget"], "#rows")
        self.assertIn("cc:toast", r["HX-Trigger-After-Settle"])

    def test_row_actions(self):
        self.client.force_login(self.w.custodian)
        r = self.client.post(reverse("catalogue:act", args=[self.w.asset.pk, "unpublish"]), HTTP_HX_REQUEST="true")
        self.assertContains(r, "Publish")
        self.w.asset.refresh_from_db()
        self.assertEqual(self.w.asset.publication_status, PublicationStatus.UNPUBLISHED)
