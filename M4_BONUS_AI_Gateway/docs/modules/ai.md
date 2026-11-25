# Module: AI Gateway (`apps/ai`)

**Delivers:** the single path to external AI (ADR-3) used by AI features 1–5 and Blueprint drafting;
AI 1 classification and photo auto-capture · Sections 9.1, 9.4, 9.5, 9.7
**Owns:** `ModelVersion`, `AIInferenceRecord`, `PolicyDocument`
**Public interface:** `gateway.AIGateway().classify / recommend_action / chat / summarize / draft_blueprint`
→ `AIResult(status, value, confidence, explanation, model_version_id, inference_id)`

## Design decisions

**D1. One gateway, swappable providers.** Modules call `AIGateway`; only `providers/*.py` import an SDK.
Switching provider or model touches one file (ADR-3 "change walk").

**D2. Every call is limited, logged and versioned.** The gateway picks the active `ModelVersion` for the
capability, applies the time limit from Table 8.2, writes an `AIInferenceRecord` (input hash, not raw data;
outcome; latency), and tags the result with the version. *Why:* Sections 9.4 and 9.7, Phase 7 AI evaluation.

**D3. The time limit really returns.** The provider runs in a worker thread and the gateway stops waiting at
the limit (`TIMEOUT`), so a slow provider never freezes a page. Tested.

**D4. Personal fields are removed before anything leaves the server** (`_redact`: email, names, user ids).
*Why:* FR-1.5 data minimisation.

**D5. Low confidence is decided by the stored threshold** of the active version, and flagged
`LOW_CONFIDENCE`; such results are never pre-accepted (FR-11.21).

**D6. Disabling a capability is a switch.** `ModelVersion.disable()` makes every call return `UNAVAILABLE`,
and callers fall back to the classic path (NFR-26). A changed threshold is a new version, never an edit.

**D7. A fake provider** gives deterministic answers for tests, offline demos and the "AI is down" walk-through.

## AI feature 1: registration suggestions (built in Step 13, optional)

**Where:** the Register asset side panel → "Suggest details with AI". It reads the name, description,
specifications and, if attached, the photo (JPG/PNG/WebP up to 5 MB), and suggests: category (only one of the
institution's own categories), 2–6 tags, a one-line standard description, the serial number (only if it is in
the text or readable on a label in the photo) and a condition guess (only from visible evidence).

**D8. Nothing is filled in automatically.** Each suggestion has its own Use / Add button; filled fields get a
soft highlight. Below the confidence threshold of the active version (0.70 in the demo) the box turns amber,
says "Not sure about these" and nothing is pre-selected (FR-11.21).

**D9. What people do with a suggestion is recorded** on the `AIInferenceRecord`: Accepted with the fields used
("category, tags"), or Ignored. Tags added from a suggestion and kept are stored with source "AI suggestion,
accepted", others as Manual (Section 9.7, for the Phase 7 AI evaluation).

**D10. The photo is sent once, as an image block.** `catalogue.services.suggest_details` base64-encodes it;
the Anthropic adapter (`classify`, prompt `CLASSIFY_SYSTEM`) sends it as an image content block next to the
text. Offline, the fake provider reads the text with the bilingual synonym table (it cannot see photos).

**D11. Unknown categories are dropped.** The reply is matched against the institution's category paths and
names; anything else becomes "Nothing confident to suggest. Pick the category yourself."

Files: `apps/catalogue/services.suggest_details`, `views.suggest` (`/assets/suggest/`), `_suggest.html`,
`_form.html`; `apps/ai/providers/anthropic.py` (`classify`), `fake.py` (`classify`); `app.js` (`data-ai-use`).

## Status of the other providers' methods

| Capability | Anthropic adapter | Fake provider |
|---|---|---|
| Summarize (AI 5, required) | Step 8 | readable paragraph from totals |
| Classify (AI 1, optional) | Step 13, with photos | text + synonyms |
| Blueprint drafting (bonus) | Step 11 | closest template |
| Recommend action (AI 3), chat (AI 4) | not planned (optional features) | unavailable / no evidence |

Still open (Phase 7 or later): an admin screen to add, activate and disable model versions (today: Django admin
or `seed_demo`).

## Tests
- OK result logged; low confidence flagged; disabled → unavailable; timeout returns within the limit;
  personal fields removed.
- `tests/test_ai_classify.py` (6): text → category, tags, serial; low confidence flagged; photo sent as an image
  and unknown categories dropped; empty input refused, requesters refused, disabled model → no suggestion; the
  screen flow stores AI-accepted vs manual tags and records "Accepted: category, tags"; the Anthropic adapter
  sends an image block and turns a bad reply into ERROR.
