# Module: Assets & Catalogue (`apps/catalogue`)

**Delivers:** C2 departments and assets, C3 publish and search · Features 4.1, 4.2, 4.4 (UC-01 to UC-06,
UC-12, UC-20 to UC-22) · BR-3, BR-7, BR-9
**Brief:** "asset-registration and inventory-management module … name, description, category, quantity, owner,
department, location, purchase date, estimated value, condition, availability, photographs, and supporting
documents"; "circular resource marketplace"; "structured search and filtering based on category, condition,
department, location, quantity, availability, asset age, estimated value, and current life cycle status".
**Owns:** `Category`, `Asset`, `AssetAttachment`, `AssetTag`

## Screens

| Screen | URL | Who |
|---|---|---|
| Browse: the marketplace grid with search and filters | `/assets/` | Everyone signed in |
| Asset side panel (or full page from a link): details, photo, tags, history, Request / Edit | `/assets/<id>/` | Everyone for published assets; the unit's custodians for the rest |
| Our assets: the custodian console, with summary counts, search and state filter | `/assets/ours/` | `asset.register` |
| Register asset / Edit asset side panels | `/assets/new/`, `/assets/<id>/edit/` | `asset.register` for the unit |
| Row actions: Confirm condition, Publish, Unpublish | `/assets/<id>/<action>/` (POST) | `asset.custody` / `asset.publish` |

## Public interface (`services.py`)

`register_asset`, `update_asset`, `change_quantity`, `confirm_condition`, `publish`, `unpublish`,
`search(...)`, `published()`, `managed_by(user)`, `campuses()`, `top_categories()`.

## Design decisions

**D1. Register → confirm condition → publish.**
A new asset is Registered and unpublished. The custodian confirms its condition (UC-12), which makes it
Available, and only then can it be published (UC-04). *Why:* Figure 7.5 starts every asset in Registered, and
BR-3 says only registered, eligible assets are published. It also stops untested items reaching the
marketplace.

**D2. The state machine lives on the model; screens never set a state.**
Every button calls a service, which calls an `Asset` operation that checks the transition. Forms have no
state or quantity-in-use fields. *Why:* Section 9.9; FR-2.16.

**D3. Permissions follow the owning unit.**
Registering, editing and publishing need the permission for the asset's owning unit (or a unit above it). The
"Owning unit" list only offers units the person covers. *Why:* BR-2 "custodians act within assigned
authority"; C1.

**D4. Quantities: lots, protected twice.**
One row can hold several identical units. "Free" = available − reserved. A miscount can be corrected, but
never below the reserved units. The database also has check constraints. *Why:* BR-7.

**D5. Classic search here; meaning-based matching in its own module.**
Search is case-insensitive keyword matching across name, description, specifications, tags, unit name and
exact serial number, combined with AND filters: category (with sub-categories), condition, campus, age, and
sort. *Why:* Section 9.10: classic search for exact lookups; NFR-1 (2 s); the Matching module (step 7) adds
ranking by meaning.

**D6. The marketplace shows only what can really be requested.**
Published, Available or partly Reserved, with at least one free unit. Unpublished assets return 404 to
people outside the owning unit. *Why:* avoids requests that can never be approved; no information leak.

**D7. Photos and documents are attachments with checks.**
JPG, PNG, WebP or PDF, at most 10 MB, numbered per asset (`attachmentNo`). The first image is the card photo;
otherwise the category icon is shown. *Why:* the brief's "photographs and supporting documents"; safe
uploads.

**D8. History is visible to everyone who can see the asset.**
The side panel shows the last ten history events (who, what, when), read from Life Cycle's table. *Why:* C6
"show for each asset who did what, and when"; transparency builds trust in reuse.

**D9. Value is per unit.** The form says "Value of one unit (AED)". *Why:* lots split on transfer; see design
change 8.

**D10. Custodian notification.** If someone registers an asset with another person as custodian, that person
gets an in-app message and an e-mail (FR-2.11).

## Added to other modules

- `apps/access/permissions.py`: `units_for(user, action)`, the units a person covers for an action.
- `apps/web/context.py`: only the longest matching menu address is highlighted.
- `apps/web/management/commands/seed_demo.py`: richer demo data (9 units, 13 categories with icons,
  13 assets on three campuses, 11 people). Run it on a fresh database.
- New migration `catalogue/0002_category_icon.py` (icon per category).

## Conflicts with earlier phases

- None. The brief lists "availability" as a field; it is derived (free units and state), not stored, so it can
  never disagree with reservations.

## Tests (`tests/test_catalogue.py`)

Registration starts Registered with history and clean tags; only custodians of the unit register; a college
custodian covers its departments; publish needs a condition check first; bad quantity and future purchase
dates are refused; photo upload works and other file types are refused; edits change descriptive fields only;
quantity cannot drop below reserved units; keyword, tag and filter search; unpublished and fully reserved
assets are hidden; Browse and the panel render; unpublished assets are hidden from others; the console is for
custodians; registering through the side panel; row actions return the updated row.

## Left for later

- "Request this" appears in the panel once the Requests module (step 4) is in.
- AI suggestions for category and tags (AI 1, step 13) will appear in the Register form.
- Arabic translations (step 12).
