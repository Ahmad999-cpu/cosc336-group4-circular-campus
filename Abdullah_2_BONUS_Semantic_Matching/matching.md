# Module: Matching Orchestration (`apps/matching`) — AI feature 2 (required)

**Delivers:** lab AI feature 2 ("for a request, list the top surplus items, each with a score and a one-line
reason; the requester accepts or rejects") · bonus feature "semantic matching" · Feature 4.12 (UC-26 to UC-28)
· ADR-5 · Section 9.2–9.3 · NFR-5, NFR-26
**Owns:** `MatchResultSet`, `MatchRecommendation`, `EmbeddingIndex`

## Screens

| Screen | URL | Who |
|---|---|---|
| **Find**: describe a need in English or Arabic; ranked results with a score ring, a one-line reason, "Why this score" (eight factor bars with points), Request, Details, Not for me (reason chips), and a switch for weaker matches | `/find/` | `request.submit` |
| **Suggested items** inside a pending request's side panel; "Choose this item" for requests made without an item | `/find/for/<request>/` (loaded into the panel) | the requester |

The home page "What do you need?" box now sends people to Find. On My requests, a pending request without an
item shows a red **Pick an item** button.

## Public interface (`services.py`)

`find(text, user, quantity, category=None)`, `generate_matches(request_id, user)`, `suggestions_for(request)`,
`current_for(request)`, `record_decision(match_id, user, decision, reason)`, `choose_for_request(match_id, user)`,
`embed_pending(limit)` (worker), `ensure_asset_embeddings(assets)`, `embed_model()`, `rank_model()`.
Each call returns an `Outcome`: `suitable`, `weak`, `ranked` (False = keyword fallback), `fallback`, `considered`.

## How a score is made

1. **Hard rules, in SQL** (`_hard_rules`): published; Available or Reserved; free units ≥ quantity asked; the
   request's category or a child category (saved requests); not the requester's own unit; not an item the
   person already turned down for the same request or the same words.
2. **Similarity**: the need and every candidate are embedded; pgvector `CosineDistance` returns the nearest.
3. **Eight factors**, each 0–1 (`engine.MatchingEngine.factors`):

| | Factor | How it is worked out |
|---|---|---|
| f1 | Similar purpose | cosine similarity, rescaled per embedder; below 0.35 the item is not a candidate |
| f2 | Specifications met | share of the must-have terms found in the item (synonyms count); a different size halves it; nothing asked = 0.7 |
| f3 | Condition fit | Any = 1; at or above the lowest acceptable = 1; one step below = 0.5; more = 0 |
| f4 | Close by | same building 1, same campus 0.8, other campus 0.4 |
| f5 | Ready by the date | 1; a Poor item 0.5 (repair first); × 0.4 if the move can't make the needed-by date |
| f6 | Low repair + transfer cost | 1 − (move AED 40 same campus / 120 other + repair 20 % of value if Poor) ÷ (value × quantity) |
| f7 | Sustainability benefit | kg CO2e avoided ÷ 100, from the most specific locally selected factor (parent categories count) |
| f8 | Enough units | 1 when the free units equal the quantity; slightly less when a big surplus serves a small need |

4. **Score = round(100 × Σ wᵢ·fᵢ)** with the Table 9.2 weights (high urgency moves 5 points from carbon to
   readiness). ≥ 70 good match, 55–69 weaker (behind a switch), < 55 not shown.
5. **Explanation** from the three biggest contributions, plus up to three "Watch:" notes (other campus, different
   size, value unknown…).

## Design decisions

**D1. Rules first, AI second.** Only items that could legally be given are scored. *Why:* Section 9.2 step 1;
the ranking can never surface something the approval transaction would refuse.

**D2. Two embedders behind one interface (conflict, see below).** `EMBEDDING_BACKEND=lexical` (default) is an
offline embedder: words, a bilingual synonym table (monitor = screen = شاشة…), related-concept families and
character trigrams, hashed into the same 384 dimensions, with Arabic normalisation (ال, ة/ه, alef forms,
diacritics, Arabic digits). `EMBEDDING_BACKEND=sentence-transformers` uses
`paraphrase-multilingual-MiniLM-L12-v2` from Phase 5. Both write to the same pgvector column; the similarity
bounds used to rescale f1 are set per embedder. If the real model cannot load, matching falls back to the lexical
one and logs a warning instead of failing. *Why:* the lab, the graders' laptops and the test suite need matching
that works with no 470 MB download and no internet; the real model stays one setting away.

**D3. Embeddings are reused until the text changes.** Each row stores a hash of the text and the model version;
the worker (`runworker`) refreshes changed items, and a search embeds any stragglers itself. *Why:* ADR-5 — fast,
private (no text leaves the server), and cost does not grow with use.

**D4. The score is arithmetic you can show.** The panel shows every factor's bar and points, the cost estimate
("Reuse costs about AED 40 … against AED 1,300 to buy new") and a confidence that says how much of the record was
filled in. The page says plainly that a score is not a probability.

**D5. Explanations come from the score, never from an LLM**, and a factor set to a middle value because the input
was missing (no specs asked, value unknown, no carbon factor) is never named as a reason. *Why:* Section 9.3.

**D6. Every run is kept and traceable.** A result set stores the ranking ModelVersion (whose `config` holds the
weights and thresholds), an input snapshot hash, and its recommendations with factor scores. A request reuses its
current set until the request, an item's `row_version`, or the settings change; then the old set is Superseded.
Each run writes an `AIInferenceRecord` (OK, NO_EVIDENCE or UNAVAILABLE). Changing weights creates a new
ModelVersion row; there is only one active per capability.

**D7. The requester's choices are recorded.** Request from a Find result or "Choose this item" = Accepted; "Not
for me" needs a reason chip (wrong size or specs, too far away, condition too poor, not what I meant, already
found one) and hides that item next time. Decisions are also copied onto the inference record (Section 9.7).

**D8. Category-only requests become approvable here.** Approval needs a specific item (Step 5). The request panel
lists suggestions; choosing one sets `selected_asset` and notifies the owning unit's approvers.

**D9. Quantity from the words.** "Two 24-inch monitors" or "شاشتان" sets the quantity to 2 when the stepper was
left at 1; "24-inch" is read as a size, not a quantity. The results say "Looking for 2 (from your words)".

**D10. Fallback is labelled.** If embedding or the vector search fails, the page shows keyword results under
"Ranking is unavailable right now … not ranked" (UC-26 E1, NFR-26).

## Added to other modules

- `apps/resource_requests/signals.py` (new) `request_sent`: sent after a request is created, so Matching can mark
  the suggestion accepted without Requests importing Matching. `views.new` passes `match` through the form.
- `resource_requests/_detail.html`: suggestions load into the panel of pending requests; `_card.html`: "Pick an item".
- `apps/web/templatetags/ui.py`: `get` and `percent` filters, `factor_label` tag.
- `static/js/app.js`: `data-fill` example chips, `data-show` switches, and `htmx:load` initialisation (fixes score
  rings that did not animate when content replaced its own placeholder). `theme.css`: match card states.
- `config/settings.py`, `.env.example`: `EMBEDDING_BACKEND`. URL prefix changed from `/matching/` to `/find/`.
- `seed_demo`: no longer creates fake EMBED/RANK model rows; Matching creates its own the first time it runs.
- Migration `0002_result_set_query`: `MatchResultSet.request` may be empty and `query_text` was added, so Find
  searches are recorded the same way as request matches.

## Conflicts with earlier phases

- **Embedding model.** Phase 5 (ADR-5) names `paraphrase-multilingual-MiniLM-L12-v2`. That model cannot be
  downloaded in our build environment, so it is **implemented but untested here**; the lexical embedder is the
  default and is what the tests cover. Before the demo, run `pip install -r requirements-ai.txt`, set
  `EMBEDDING_BACKEND=sentence-transformers`, run `python manage.py runworker --once`, and check the Find page.
  The bounds in `engine.SIMILARITY_BOUNDS` for that model are a starting point; adjust them after trying 10–20
  real searches.
- **Result sets without a request.** The class diagram ties `MatchResultSet` to a `ResourceRequest`. The lab
  flow and the prototype start from Find, before a request exists, so `request` is now optional and the search
  text is stored instead.
- **"Mandatory specs" as a hard rule** (Phase 5 D1). Free text has no reliable "must have" list, so specs are a
  scored factor (f2) with the size check, not a filter. Nothing is hidden for a missing word.

## Tests (`tests/test_matching.py`, 31 tests)

Arabic normalisation and synonyms; unit-length 384-wide vectors; "display screen" closer to "monitor" than to
"chair" (and the Arabic equivalent); quantity read from words; weights sum to 1; score arithmetic; weak results
dropped; explanations never cite a neutral factor; each factor (location, condition, specs and size, cost and
unknown value, tight date, irrelevance cut-off); Find ranks, excludes own unit / unpublished / unrelated, logs
the inference and the ModelVersion config; Arabic query finds an English item; quantity hard rule; no-match and
fallback outcomes; embeddings reused until the text changes; one active ModelVersion and a new row when weights
change; carbon factor from a parent category; request suggestions reused then superseded; choose sets the item,
records acceptance and notifies approvers; only the requester decides; "Not for me" needs a reason and hides the
item; screens (Find page and partial, request-from-match counted as accepted, choose over HTMX, 404 for someone
else's suggestion, 403 for people who cannot request).
