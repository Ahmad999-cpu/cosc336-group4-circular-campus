# Phase 8: Bulk asset registration from CSV

**Module:** Catalogue (`apps/catalogue/bulk.py`, model `ImportBatch`) · **Migration:** `catalogue 0005_import_batch` ·
**Screens:** **Import from CSV** on Our assets, then `/assets/import/` (upload), `/assets/import/template.csv` and
`/assets/import/<id>/` (preview, then result) · **Who:** `asset.register`, and only for the units the person manages.

## Flow

1. **Download the template.** It is UTF-8 with a BOM, so Excel keeps Arabic text, and it has one example row.
   - Required columns: `name, category, unit, quantity, condition, campus`.
   - Optional columns: `building, room, value_aed, purchase_date (YYYY-MM-DD), serial_number, external_ref,
     description, specifications, tags`.
2. **Upload.** Every row is checked and nothing is saved. The preview shows each row as **OK**, **Error** with
   plain messages ("Row 5, quantity: must be a whole number from 1 to 10,000"), or **Possible duplicate**, which
   has an "Import anyway" box ticked by default.
3. **Confirm.** Valid rows are registered. Rows with errors are skipped, and the result page lists them with the
   reason so they can be fixed and uploaded in a separate file. Valid rows don't wait for invalid ones.

## Design decisions

**B1. Same rules as one-by-one registration.** Each row goes through `services.register_asset`. That function
checks the permission for the row's unit, validates the data, writes the registration history and the audit
log entry, and notifies the custodian. Each row runs in its own savepoint, so a row that fails at import time
(for example, a permission removed between preview and confirm) doesn't stop the others.

**B2. Never published by default.** Imported items are **Registered and unpublished**, as with the normal
workflow (register, confirm condition, publish). The person can tick "Also confirm their condition as listed and
publish them". The box is offered only when they hold both `asset.custody` and `asset.publish` for every unit in
the file, and it calls the normal `confirm_condition` and `publish` services.

**B3. Duplicates, explained.**
- **The same file twice:** the SHA-256 of the file text is kept. If an identical file was already imported, the
  upload is refused with the date it was imported.
- **The same batch twice:** confirming locks the batch row. A second click or a resent form finds it Imported
  and imports nothing.
- **Row errors:** the serial number or the external register ID already exists in that unit, or the same serial
  number appears twice in the file.
- **Row warnings:** the same name, campus, building and room as an item already in that unit. It is imported
  only if left ticked.

**B4. File safety.**
- `.csv` only, and at most **1 MB** and **500 rows**.
- Must be UTF-8 (a BOM is fine). Binary files are refused.
- Malformed CSV gives a plain error, not a crash, and so do missing required columns.
- Rows with more values than columns are rejected ("check for a stray comma").
- Field length limits are the same as the model's.
- The uploaded file is not stored. Only the parsed rows are kept, for the preview.

**B5. Categories and units by name.** A category can be given by name or by path ("IT Equipment / Monitors"). A
unit is matched by name only within the units the person manages. For a unit outside their scope the message is
"you can't register assets for 'ME'". For an unknown unit it is "'Mars' is not a unit".

**B6. Course scope.** This imports test data entered by custodians. It is not an integration with KU's official
registers, which Phases 1–2 put out of scope (see `docs/design-changes.md`).

## Tests

`tests/test_bulk_import.py` covers:
- the template;
- that the preview writes nothing;
- that import uses the normal workflow (history, audit, tags);
- per-row and per-field errors, with valid rows imported on their own;
- serial number, register ID, in-file and name-and-place duplicates, including skipping an unticked duplicate;
- a batch imports once and the same file is refused later;
- publishing only when chosen and allowed;
- file safety: wrong type, not UTF-8, too large, missing columns, empty, too many rows, extra values;
- permissions;
- the screens, including a double click.
