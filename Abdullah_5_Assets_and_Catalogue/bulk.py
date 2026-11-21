"""Phase 8: register many assets from a CSV file.

Two steps, both checked on the server:
1. `check_file`: read and validate every row, without writing any asset; the rows and their problems are kept in
   an ImportBatch so the person sees a preview.
2. `import_batch`: register the valid rows through `services.register_asset` (the same rules, history and audit as
   one-by-one registration). Rows with errors are skipped and listed. Items stay Registered and unpublished
   unless the person ticks "confirm condition and publish" and may do both for every unit in the file.

Duplicates: an identical file that was already imported is refused; a row whose serial number or register ID
already exists in that unit (or appears twice in the file) is an error; a row with the same name and place as an
existing item is a warning ("possible duplicate"), imported only if the person keeps it ticked.
"""
from __future__ import annotations

import csv
import hashlib
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.access.models import Department, User
from apps.access.permissions import can, units_for
from apps.audit.services import record
from apps.common.enums import Condition
from apps.common.errors import Forbidden, ValidationFailed

from . import services
from .models import Asset, Category, ImportBatch, ImportStatus

MAX_BYTES = 1024 * 1024
MAX_ROWS = 500
MAX_QTY = 10000
REQUIRED = ["name", "category", "unit", "quantity", "condition", "campus"]
OPTIONAL = ["building", "room", "value_aed", "purchase_date", "serial_number", "external_ref", "description", "specifications", "tags"]
COLUMNS = REQUIRED + OPTIONAL
LIMITS = {"name": 200, "campus": 100, "building": 100, "room": 50, "serial_number": 120, "external_ref": 120,
          "description": 2000, "specifications": 2000, "tags": 500}
TYPES = {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream", ""}

EXAMPLE = {"name": "Dell 24-inch monitor", "category": "IT Equipment / Monitors", "unit": "Computer Science", "quantity": "4",
           "condition": "GOOD", "campus": "Main", "building": "B1", "room": "1.12", "value_aed": "650",
           "purchase_date": "2023-05-01", "serial_number": "CN-0X1234", "external_ref": "", "description": "24-inch IPS monitor",
           "specifications": "24 in, 1920x1080, HDMI, DisplayPort", "tags": "monitor, 24-inch"}


def template_csv() -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\r\n")
    w.writeheader()
    w.writerow(EXAMPLE)
    return "﻿" + buf.getvalue()  # BOM: Excel opens Arabic text correctly


def _require_any(user: User) -> None:
    if not units_for(user, "asset.register").exists():
        raise Forbidden("Not permitted: asset.register")


def _read(upload) -> tuple[str, str]:
    name = (getattr(upload, "name", "") or "").strip()
    if not name.lower().endswith(".csv"):
        raise ValidationFailed("Upload a .csv file (save the spreadsheet as CSV UTF-8 first)")
    if (getattr(upload, "content_type", "") or "").split(";")[0] not in TYPES:
        raise ValidationFailed("Upload a .csv file (save the spreadsheet as CSV UTF-8 first)")
    if upload.size > MAX_BYTES:
        raise ValidationFailed("The file is larger than 1 MB. Split it into smaller files")
    raw = upload.read(MAX_BYTES + 1)
    if b"\x00" in raw:
        raise ValidationFailed("This doesn't look like a CSV text file. Save the spreadsheet as CSV UTF-8 and try again")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationFailed("The file is not UTF-8 text. In Excel use Save As, then CSV UTF-8")
    return name[:200], text


def _category(value: str, cats: dict) -> Category | None:
    v = " / ".join(p.strip() for p in value.split("/")).lower()
    return cats["path"].get(v) or cats["name"].get(v.split(" / ")[-1]) if v else None


def check_file(user: User, upload) -> ImportBatch:
    """Validate every row and keep the result for the preview. Writes no assets."""
    _require_any(user)
    name, text = _read(upload)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    earlier = ImportBatch.objects.filter(file_sha256=digest, status=ImportStatus.IMPORTED).first()
    if earlier is not None:
        message = _("This exact file was already imported on %(d)s. Nothing was imported again.") % {
            "d": timezone.localtime(earlier.imported_at).strftime("%d %b %Y %H:%M")}
        raise ValidationFailed(message)
    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
        rows = list(reader)
    except csv.Error as exc:
        message = _("The file could not be read as CSV: %(e)s") % {"e": str(exc)[:120]}
        raise ValidationFailed(message)
    missing = [c for c in REQUIRED if c not in headers]
    if missing:
        message = _("Missing columns: %(c)s. Download the template to see the expected columns.") % {"c": ", ".join(missing)}
        raise ValidationFailed(message)
    if not rows:
        raise ValidationFailed("The file has a header row but no assets")
    if len(rows) > MAX_ROWS:
        raise ValidationFailed("The file has more than 500 rows. Split it into smaller files")

    cats = {"path": {}, "name": {}}
    for c in Category.objects.select_related("parent"):
        cats["path"][c.path().lower()] = c
        cats["name"].setdefault(c.name.lower(), c)
    allowed = {d.name.lower(): d for d in units_for(user, "asset.register")}
    known = {d.name.lower() for d in Department.objects.all()}
    seen_serials, out = {}, []
    for i, raw in enumerate(rows, start=2):  # row 1 is the header
        v = {(k or "").strip().lower(): (val or "").strip() for k, val in raw.items() if k is not None}
        if None in raw and any((x or "").strip() for x in (raw.get(None) or [])):
            out.append({"n": i, "values": {c: v.get(c, "") for c in COLUMNS},
                        "errors": [_("Row %(n)s has more values than columns: check for a stray comma.") % {"n": i}], "warnings": []})
            continue
        if not any(v.get(c) for c in COLUMNS):
            continue  # blank line
        errs, warns = [], []

        def err(field, text):
            errs.append(_("Row %(n)s, %(f)s: %(t)s") % {"n": i, "f": field, "t": text})

        for c in REQUIRED:
            if not v.get(c):
                err(c, _("required"))
        for c, n in LIMITS.items():
            if len(v.get(c, "")) > n:
                err(c, _("at most %(n)s characters") % {"n": n})
        cat = _category(v.get("category", ""), cats)
        if v.get("category") and cat is None:
            err("category", _("\"%(v)s\" is not a category. Use a name or path from the template, e.g. IT Equipment / Monitors.") % {"v": v["category"][:60]})
        unit = allowed.get(v.get("unit", "").lower())
        if v.get("unit") and unit is None:
            err("unit", _("you can't register assets for \"%(v)s\"") % {"v": v["unit"][:60]} if v["unit"].lower() in known
                else _("\"%(v)s\" is not a unit") % {"v": v["unit"][:60]})
        qty = None
        if v.get("quantity"):
            try:
                qty = int(v["quantity"])
                if not 1 <= qty <= MAX_QTY:
                    raise ValueError
            except ValueError:
                err("quantity", _("must be a whole number from 1 to 10,000"))
        cond = v.get("condition", "").upper()
        if v.get("condition") and cond not in Condition.values:
            err("condition", _("must be NEW, GOOD, FAIR or POOR"))
        value = None
        if v.get("value_aed"):
            try:
                value = Decimal(v["value_aed"].replace(",", ""))
                if value < 0 or value > Decimal("9999999999"):
                    raise InvalidOperation
            except InvalidOperation:
                err("value_aed", _("must be a number of AED, 0 or more"))
        bought = None
        if v.get("purchase_date"):
            try:
                bought = date.fromisoformat(v["purchase_date"])
                if bought > timezone.localdate():
                    err("purchase_date", _("can't be in the future"))
            except ValueError:
                err("purchase_date", _("use the form YYYY-MM-DD, e.g. 2023-05-01"))
        serial, ref = v.get("serial_number", ""), v.get("external_ref", "")
        if serial:
            if serial.lower() in seen_serials:
                err("serial_number", _("also on row %(m)s of this file") % {"m": seen_serials[serial.lower()]})
            seen_serials.setdefault(serial.lower(), i)
            if unit and Asset.objects.filter(owner_department=unit, serial_number__iexact=serial).exists():
                err("serial_number", _("an asset with this serial number is already registered in this unit"))
        if ref and unit and Asset.objects.filter(owner_department=unit, external_ref__iexact=ref).exists():
            err("external_ref", _("an asset with this register ID is already registered in this unit"))
        if not errs and unit and Asset.objects.filter(owner_department=unit, name__iexact=v["name"], location_campus__iexact=v["campus"],
                                                      location_building__iexact=v.get("building", ""), location_room__iexact=v.get("room", "")).exists():
            warns.append(_("Row %(n)s: possible duplicate, an item with the same name and place is already registered in %(u)s.") % {"n": i, "u": unit.name})
        out.append({"n": i, "values": {c: v.get(c, "") for c in COLUMNS}, "errors": errs, "warnings": warns,
                    "clean": None if errs else {"category": str(cat.pk), "unit": str(unit.pk), "quantity": qty, "condition": cond,
                                                "value": str(value) if value is not None else None,
                                                "bought": bought.isoformat() if bought else None}})
    if not out:
        raise ValidationFailed("The file has a header row but no assets")
    batch = ImportBatch.objects.create(uploaded_by=user, file_name=name, file_sha256=digest, rows=out)
    record(user, "bulk_import_checked", "ImportBatch", batch.pk,
           after={"file": name, "rows": len(out), "errors": len(batch.error_rows)})
    return batch


def can_publish_all(user: User, batch: ImportBatch) -> bool:
    units = {r["clean"]["unit"] for r in batch.valid_rows}
    depts = Department.objects.filter(pk__in=units)
    return bool(units) and all(can(user, "asset.publish", d) and can(user, "asset.custody", d) for d in depts)


def import_batch(user: User, batch_id, *, skip_rows=(), publish: bool = False) -> ImportBatch:
    """Register the valid rows. Each row is its own savepoint, so one failure doesn't stop the others.
    A batch is imported at most once (the row lock makes a double click a no-op)."""
    with transaction.atomic():
        batch = ImportBatch.objects.select_for_update().get(pk=batch_id)
        if batch.uploaded_by_id != user.pk:
            raise Forbidden("Only the person who uploaded this file can import it")
        if batch.status == ImportStatus.IMPORTED:
            raise ValidationFailed("This file was already imported. Nothing was imported twice")
        if batch.status != ImportStatus.PREVIEW:
            raise ValidationFailed("This upload was discarded. Upload the file again")
        if publish and not can_publish_all(user, batch):
            raise Forbidden("You can't publish items for every unit in this file. Import without publishing")
        skip = {int(n) for n in skip_rows}
        imported, failed, published = [], [], 0
        cats = {str(c.pk): c for c in Category.objects.all()}
        for r in batch.rows:
            if r["errors"]:
                failed.append({"n": r["n"], "error": "; ".join(r["errors"])})
                continue
            if r["n"] in skip:
                failed.append({"n": r["n"], "error": _("Skipped: you unticked this possible duplicate.")})
                continue
            v, c = r["values"], r["clean"]
            data = {"name": v["name"], "category": cats.get(c["category"]), "owner_department": Department.objects.get(pk=c["unit"]),
                    "quantity": c["quantity"], "condition": c["condition"], "location_campus": v["campus"],
                    "location_building": v["building"], "location_room": v["room"],
                    "estimated_value": Decimal(c["value"]) if c["value"] else None,
                    "purchase_date": date.fromisoformat(c["bought"]) if c["bought"] else None,
                    "serial_number": v["serial_number"], "external_ref": v["external_ref"],
                    "description": v["description"], "specifications": v["specifications"]}
            try:
                with transaction.atomic():
                    a = services.register_asset(user, data, tags=v.get("tags", ""))
                    if publish:
                        a = services.confirm_condition(user, a, a.condition)
                        services.publish(user, a)
                        published += 1
                imported.append({"n": r["n"], "asset": str(a.pk), "name": a.name})
            except (ValidationFailed, Forbidden) as exc:
                failed.append({"n": r["n"], "error": str(exc)})
        batch.status, batch.imported_at = ImportStatus.IMPORTED, timezone.now()
        batch.result = {"imported": imported, "failed": failed, "published": published}
        batch.save(update_fields=["status", "imported_at", "result"])
        record(user, "bulk_import", "ImportBatch", batch.pk,
               after={"file": batch.file_name, "imported": len(imported), "failed": len(failed), "published": published})
    return batch


def discard(user: User, batch: ImportBatch) -> None:
    if batch.uploaded_by_id != user.pk:
        raise Forbidden("Only the person who uploaded this file can discard it")
    if batch.status == ImportStatus.PREVIEW:
        batch.status = ImportStatus.DISCARDED
        batch.save(update_fields=["status"])
