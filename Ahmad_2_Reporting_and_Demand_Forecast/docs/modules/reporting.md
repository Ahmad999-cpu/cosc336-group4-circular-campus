# Module: Reporting (`apps/reporting`): C9 and AI feature 5 (required)

**Delivers:**
- **C9:** a table of requests and transfers with CSV export.
- **Lab AI feature 5:** "the database calculates the numbers, the AI writes a short summary, the admin edits it
  before publishing".
- Feature 4.13 (UC-39 to UC-41), FR-15.13, FR-15.14, Section 9.10.

**Owns:** `Report`, `AISummary`.

## Screen

| Screen | URL | Who |
|---|---|---|
| **Reports** page | `/reports/` | `reports.view` (limited to the person's units) |
| CSV download (same filters) | `/reports/csv/` | `reports.view` |
| Write an AI draft, then publish or discard it | `/reports/summary/…` | `reports.publish` |

The Reports page has:
- a report switch (Requests and transfers / Available items);
- period and unit filters, which update the page without reloading;
- four number tiles and the Summary panel;
- the table (newest 100 rows; the CSV has all of them).

## Public interface (`services.py`)

- `Filters` (type, start, end, unit) and `build(user, filters)`. `build` returns (columns, rows, totals) and is
  used by both the screen and the CSV.
- `requests_transfers_rows`, `requests_transfers_totals`, `available_assets_rows`, `available_assets_totals`.
- `export_csv`, `summary_input`, `generate_summary`, `publish_summary`, `discard_summary`, `summaries_for`.
- `unchecked_numbers`, `edit_distance_share`.

## What the C9 report shows

**Requests and transfers:** one row per request in the period, with its unit, category, quantity, status, item,
who decided it, and the transfer's status with dispatch and receipt times.

The tiles show:
- requests and units asked for, with the median hours to a decision;
- the approval rate (approved ÷ decided), with the approved, rejected and waiting counts;
- units moved by completed transfers, with how many are on the way;
- value reused (received units × the item's estimated value) and planned purchases avoided.

**Available items:** published items with free units by unit, category, campus, condition and value. The tiles
show items listed, free units, value waiting for reuse and items under maintenance.

## Design decisions

**D1. Numbers come only from the database.**
- `build()` computes every total.
- The AI receives those totals plus at most 200 rows, and returns text only.
- *Why:* FR-15.13 and Section 9.10.

**D2. Every number in an AI draft is checked.**
- `unchecked_numbers` lists any number in the draft that is not a total or a period date.
- The editor sees "These numbers are not in the report: …" before publishing.
- *Why:* a language model can invent or recompute figures, and the person publishing needs to see where.

**D3. Always a draft first, only editors publish.**
- `reports.publish` is needed to write and publish a draft; `reports.view` only shows published summaries.
- A draft is visible only to the person who generated it until it is published.
- Published text is stored next to the AI's draft, and the page says whether it was edited.
  `edit_distance_share` measures how much people changed (for the Phase 7 AI evaluation).

**D4. The report works without AI.**
- A timeout, an outage or an unreadable reply leaves the tiles, table and CSV untouched.
- The panel shows a clear message, and no empty summary is saved (FR-15.14).

**D5. A summary is tied to its numbers.**
- Each draft saves a `Report` with the filters, period and data cut-off.
- A published summary shows "Numbers as of …".
- A summary appears only for the exact filters it was written for.

**D6. No names leave the server.**
- The "Decided by" column is removed from the rows sent to the AI, on top of the gateway's own redaction (FR-1.5).
- The panel says so under the draft.

**D7. Summaries follow the interface language.**
- `summary_input` passes the current language; the prompt asks for Modern Standard Arabic when it is `ar`.

**D8. The CSV opens cleanly in Excel.**
- It starts with a UTF-8 BOM, so Arabic names display correctly.
- Every export is recorded (a `Report` row with `exported_at`, plus an audit entry).

**D9. Scope follows permissions.**
- People see only units where they hold `reports.view` (and units below them).
- Picking a unit outside that scope is refused.

## The AI adapter (`apps/ai/providers/anthropic.py`)

**Prompt:**
- The system prompt is fixed: only numbers from `totals`, 80 to 140 words, no markdown, one limitation, neutral
  tone, no names.
- The reply must be JSON (`{"text", "claims"}`).

**Model:**
- `ANTHROPIC_MODEL` (default `claude-haiku-5-5`), unless the active ModelVersion was created for Anthropic.

**Parsing:**
- The adapter takes the first JSON object in the reply.
- Anything else becomes `ERROR`, never an exception.

**Turning it on:**
- `pip install -r requirements-ai.txt`.
- In `.env`, set `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=…`.
- Run `seed_demo` on a fresh database, or add an active SUMMARIZE ModelVersion with provider `anthropic`.

**Without a key**, the fake provider writes a plain paragraph from the totals, so the whole review flow can be
demonstrated offline.

## Added to other modules

- **AI:**
  - `apps/ai/providers/anthropic.py`: `summarize` implemented.
  - `apps/ai/providers/fake.py`: a readable demo paragraph.
- **Settings:** `config/settings.py` and `.env.example` gain `ANTHROPIC_MODEL`.
- **Seed data:** `seed_demo` creates the SUMMARIZE model for the configured provider.
- **Web:**
  - `apps/web/templatetags/ui.py` gains the icons `spark`, `download` and `alert`.
  - `theme.css` gains radio-button segments, the summary panel and busy states.
- **Bug fixes found while testing:**
  - `transfers/services.transfer_for_request` now orders by reservation time. It used to order by UUID, which is
    random.
  - Find and Reports decide "partial page or full page" from the `HX-Target` header. Previously `?partial=1` was
    pushed into the address bar.

## Conflicts with earlier phases

- **Who publishes.** The lab slide says "the admin edits it before publishing". Our role table gives
  `reports.publish` to the Sustainability Officer, not the System Administrator, who manages users and settings.
  The demo keeps it that way, and Blueprint can give the permission to any role.
- **Which reports.** Phase 4 lists five report types. Phase 6 builds Requests and transfers (C9) and Available
  items. Sustainability figures are on the Sustainability dashboard (Step 10). Maintenance history is on the
  Maintenance board. AI quality is part of the Phase 7 evaluation.

## Tests (`tests/test_reporting.py`, 13 tests)

- **Data:**
  - totals worked out from a real approve → dispatch → receive → reject flow;
  - CSV header and rows match the screen, and the export is recorded;
  - period filter; scope (no permission, and a unit above the person's scope);
  - Available items totals.
- **Summary flow:**
  - draft → edit → publish; no second publish; viewers see the published text;
  - invented numbers are flagged;
  - the AI input has no names and at most 200 rows;
  - an AI timeout leaves the report working and saves no summary;
  - only editors write, publish or discard;
  - very short text is refused.
- **Anthropic adapter, with the network call mocked:**
  - the configured model and the "use only numbers" prompt are used;
  - bad replies become errors, not exceptions.
- **Screens:**
  - page, partial update, CSV download, and the summarize and publish flow over HTMX;
  - no AI button for viewers; 403 for people without `reports.view`.
