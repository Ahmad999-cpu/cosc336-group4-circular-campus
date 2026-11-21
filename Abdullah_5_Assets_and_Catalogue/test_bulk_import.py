"""Phase 8: bulk asset registration from CSV."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalogue import bulk
from apps.catalogue.models import Asset, AssetState, Category, ImportBatch, ImportStatus, PublicationStatus
from apps.common.errors import Forbidden, ValidationFailed
from apps.lifecycle.models import LifeCycleEvent

from .factories import World

HEAD = "name,category,unit,quantity,condition,campus,building,room,value_aed,purchase_date,serial_number,external_ref,description,specifications,tags\n"


def f(body: str, name="assets.csv", head=HEAD, ctype="text/csv"):
    return SimpleUploadedFile(name, (head + body).encode("utf-8"), content_type=ctype)


class BulkImportTests(TestCase):
    def setUp(self):
        self.w = World()
        self.it = Category.objects.create(name="IT Equipment")
        self.mon = Category.objects.create(name="Monitors 2", parent=self.it)

    def test_template_has_columns_and_an_example(self):
        t = bulk.template_csv()
        self.assertTrue(t.startswith("﻿name,category,unit,quantity"))
        self.assertIn("Dell 24-inch monitor", t)

    def test_preview_then_import_registers_through_the_normal_workflow(self):
        b = bulk.check_file(self.w.custodian, f(
            "HP 24 monitor,IT Equipment / Monitors 2,CS,3,good,Main,B1,1.2,600,2022-01-05,SN-1,,desc,24 in,\"monitor, hp\"\n"
            "Desk lamp,Monitors,CS,1,FAIR,Main,,,,,,,,,\n"))
        self.assertEqual(Asset.objects.count(), 1)  # only the World monitor: nothing written by the check
        self.assertEqual((len(b.valid_rows), len(b.error_rows)), (2, 0))
        b = bulk.import_batch(self.w.custodian, b.pk)
        self.assertEqual(len(b.result["imported"]), 2)
        a = Asset.objects.get(name="HP 24 monitor")
        self.assertEqual((a.lifecycle_state, a.publication_status), (AssetState.REGISTERED, PublicationStatus.UNPUBLISHED))
        self.assertEqual(a.category, self.mon)
        self.assertEqual(sorted(a.tags.values_list("tag_text", flat=True)), ["hp", "monitor"])
        self.assertTrue(LifeCycleEvent.objects.filter(asset=a, event_type="REGISTRATION").exists())
        self.assertTrue(AuditLog.objects.filter(action="bulk_import").exists())
        self.assertTrue(AuditLog.objects.filter(action="register_asset", entity_id=a.pk).exists())

    def test_errors_name_the_row_and_field_and_valid_rows_import_alone(self):
        b = bulk.check_file(self.w.custodian, f(
            "Good row,Monitors 2,CS,2,GOOD,Main,,,,,,,,,\n"
            ",Nope,Mars,zero,SHINY,,,,-5,2099-01-01,,,,,\n"
            "Other unit row,Monitors 2,ME,1,GOOD,Main,,,,,,,,,\n"))
        bad = b.error_rows[0]["errors"]
        text = " ".join(bad)
        for part in ("Row 3, name: required", "Row 3, category:", "Row 3, unit: \"Mars\" is not a unit", "Row 3, quantity: must be a whole number",
                     "Row 3, condition: must be NEW, GOOD, FAIR or POOR", "Row 3, value_aed:", "Row 3, purchase_date: can't be in the future"):
            self.assertIn(part, text)
        self.assertIn("Row 4, unit: you can't register assets for \"ME\"", " ".join(b.error_rows[1]["errors"]))
        b = bulk.import_batch(self.w.custodian, b.pk)
        self.assertEqual(len(b.result["imported"]), 1)
        self.assertEqual([x["n"] for x in b.result["failed"]], [3, 4])

    def test_duplicates(self):
        Asset.objects.filter(pk=self.w.asset.pk).update(serial_number="SN-9")
        b = bulk.check_file(self.w.custodian, f(
            "A,Monitors 2,CS,1,GOOD,Main,,,,,SN-9,,,,\n"
            "B,Monitors 2,CS,1,GOOD,Main,,,,,SN-2,,,,\n"
            "C,Monitors 2,CS,1,GOOD,Main,,,,,sn-2,,,,\n"
            "Dell monitor,Monitors 2,CS,1,GOOD,Main,B1,1.12,,,,,,,\n"))
        errs = {r["n"]: " ".join(r["errors"]) for r in b.rows}
        self.assertIn("already registered in this unit", errs[2])
        self.assertIn("also on row 3 of this file", errs[4])
        self.assertEqual([r["n"] for r in b.warning_rows], [5])  # same name and place as the World monitor
        b = bulk.import_batch(self.w.custodian, b.pk, skip_rows=[5])
        self.assertEqual([x["n"] for x in b.result["imported"]], [3])
        self.assertIn("Skipped", next(x for x in b.result["failed"] if x["n"] == 5)["error"])

    def test_a_batch_imports_once_and_the_same_file_is_refused_later(self):
        body = "Once,Monitors 2,CS,1,GOOD,Main,,,,,,,,,\n"
        b = bulk.check_file(self.w.custodian, f(body))
        bulk.import_batch(self.w.custodian, b.pk)
        with self.assertRaises(ValidationFailed):
            bulk.import_batch(self.w.custodian, b.pk)
        with self.assertRaises(ValidationFailed):
            bulk.check_file(self.w.custodian, f(body))
        self.assertEqual(Asset.objects.filter(name="Once").count(), 1)

    def test_publish_only_when_chosen_and_allowed(self):
        b = bulk.check_file(self.w.custodian, f("Pub,Monitors 2,CS,2,GOOD,Main,,,,,,,,,\n"))
        self.assertTrue(bulk.can_publish_all(self.w.custodian, b))
        bulk.import_batch(self.w.custodian, b.pk, publish=True)
        a = Asset.objects.get(name="Pub")
        self.assertEqual((a.lifecycle_state, a.publication_status), (AssetState.AVAILABLE, PublicationStatus.PUBLISHED))

    def test_file_safety(self):
        cases = [
            SimpleUploadedFile("x.xlsx", b"PK\x03\x04", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            SimpleUploadedFile("x.csv", b"\xff\xfe\x00n\x00a", content_type="text/csv"),
            SimpleUploadedFile("x.csv", b"a" * (bulk.MAX_BYTES + 10), content_type="text/csv"),
            f("", head="name,unit\n"),
            f(""),
            f("".join(f"R{i},Monitors 2,CS,1,GOOD,Main,,,,,,,,,\n" for i in range(bulk.MAX_ROWS + 1))),
        ]
        for up in cases:
            with self.assertRaises(ValidationFailed):
                bulk.check_file(self.w.custodian, up)
        b = bulk.check_file(self.w.custodian, f("Extra,Monitors 2,CS,1,GOOD,Main,,,,,,,,,,,surplus\n"))
        self.assertIn("more values than columns", b.rows[0]["errors"][0])

    def test_permissions(self):
        with self.assertRaises(Forbidden):
            bulk.check_file(self.w.requester, f("X,Monitors 2,CS,1,GOOD,Main,,,,,,,,,\n"))
        b = bulk.check_file(self.w.custodian, f("X,Monitors 2,CS,1,GOOD,Main,,,,,,,,,\n"))
        with self.assertRaises(Forbidden):
            bulk.import_batch(self.w.approver, b.pk)


class BulkScreenTests(TestCase):
    def setUp(self):
        self.w = World()
        self.client.force_login(self.w.custodian)

    def test_full_flow(self):
        self.assertContains(self.client.get(reverse("catalogue:mine")), "Import from CSV")
        t = self.client.get(reverse("catalogue:import_template"))
        self.assertEqual(t["Content-Type"], "text/csv; charset=utf-8")
        r = self.client.post(reverse("catalogue:import"), {"file": f("Lamp,Monitors,CS,2,GOOD,Main,,,,,,,,,\nBad,Monitors,CS,0,GOOD,Main,,,,,,,,,\n")})
        b = ImportBatch.objects.get()
        self.assertRedirects(r, reverse("catalogue:import_batch", args=[b.pk]))
        page = self.client.get(reverse("catalogue:import_batch", args=[b.pk]))
        self.assertContains(page, "Import 1 valid row")
        self.assertContains(page, "Row 3, quantity")
        self.client.post(reverse("catalogue:import_batch", args=[b.pk]), {"action": "import"})
        self.client.post(reverse("catalogue:import_batch", args=[b.pk]), {"action": "import"})  # double click
        self.assertEqual(Asset.objects.filter(name="Lamp").count(), 1)
        done = self.client.get(reverse("catalogue:import_batch", args=[b.pk]))
        self.assertContains(done, "Import result")
        self.assertContains(done, "Rows not imported")

    def test_bad_upload_is_explained(self):
        r = self.client.post(reverse("catalogue:import"), {"file": SimpleUploadedFile("x.txt", b"hi", content_type="text/plain")})
        self.assertContains(r, "Upload a .csv file", status_code=400)

    def test_others_cannot_see_a_batch_or_import(self):
        b = bulk.check_file(self.w.custodian, f("Lamp,Monitors,CS,2,GOOD,Main,,,,,,,,,\n"))
        self.client.force_login(self.w.requester)
        self.assertEqual(self.client.get(reverse("catalogue:import")).status_code, 403)
        self.assertEqual(self.client.get(reverse("catalogue:import_batch", args=[b.pk])).status_code, 403)
