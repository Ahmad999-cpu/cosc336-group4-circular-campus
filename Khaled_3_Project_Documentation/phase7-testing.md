# Phase 7: testing and evaluation (draft for the report)

This file is the material for the Phase 7 report: what is tested, how to run it, how each lab requirement is
covered, and how the two required AI features were evaluated. Numbers were measured on 14 Nov 2026 on the demo
data (`python manage.py seed_demo`) with the offline lexical embedder and the fake AI provider.

## How to run

```bash
python manage.py test                       # 187 tests, about 2 minutes (add --parallel 4 to halve it)
coverage run --source=apps --omit="*/migrations/*,apps/*/admin.py" manage.py test && coverage report
python manage.py evaluate_matching --out docs/evaluation/matching.md
```

Tests use Django's test runner with a real PostgreSQL test database (the same engine as production, so row
locks, `select_for_update` and pgvector behave as they will in the pilot).

## What kind of tests

| Level | What it checks | Examples |
|---|---|---|
| **Unit** | one rule or formula, no database where possible | score = Σ wᵢfᵢ; weights sum to 1; calculator worked example; state-machine transitions; Arabic normalisation |
| **Service / integration** | a whole use case through the public `services.py` of a module, with the database | approve → reserve → dispatch → receive → impact recorded; concurrent approvals; draft → publish summary |
| **Screen** | the Django view, template and HTMX behaviour through the test client | partial swaps (`HX-Target`), `HX-Redirect`, toasts (`HX-Trigger`), 403 for the wrong role, 404 for someone else's object |
| **Contract (AI)** | the AI adapters with the network call replaced | the prompt and model used; image block sent once; bad replies become `ERROR`, never an exception |
| **Evaluation** | quality of AI output against labelled data | matching relevance (below) |

Browser-level checks (Playwright) were run by hand for every screen in English and Arabic during the build; they
are not part of the automated suite because they need a browser in CI.

## Test inventory (187 tests)

| File | Tests | Covers |
|---|---|---|
| `test_access.py` | 13 | sign-in, sessions, people, roles, last-admin protection (C1) |
| `test_catalogue.py` | 15 | register, edit, confirm condition, publish/unpublish, search and filters (C2, C3) |
| `test_requests.py` | 10 | submit (idempotent), edit, cancel, rules (C4) |
| `test_approvals.py` | 8 | approval routing, limits, self-approval (C5) |
| `test_transfers.py` | 14 | approve/reject, reservation, dispatch, delivery events, receipt, discrepancy, concurrency (C5) |
| `test_lifecycle.py` | 11 | history, allowed moves, maintenance cycle, end of life with independent review (C6) |
| `test_state_machines.py` | 8 | every state machine refuses illegal moves (C6) |
| `test_notifications.py` | 9 | made / approved / rejected / received notify the right people; e-mail failure never blocks (C8) |
| `test_reporting.py` | 13 | C9 rows, totals and CSV; AI 5 draft → edit → publish; numbers check; AI down (C9, AI 5) |
| `test_matching.py` | 31 | embeddings, eight factors, hard rules, ranking, explanations, fallback, decisions (AI 2) |
| `test_sustainability.py` | 10 | impact on receipt, dashboard with formulas and "unavailable", net cost (C7, bonus) |
| `test_calculator.py` | 4 | cost-avoidance calculator worked example and price bands (bonus) |
| `test_blueprint.py` | 15 | units, member types, routes, tester, templates, AI drafts (bonus) |
| `test_i18n.py` | 6 | Arabic RTL, translations complete, bilingual notifications, number formats (bonus) |
| `test_ai_gateway.py` | 5 | logging, low confidence, disabled model, time limit, redaction |
| `test_ai_classify.py` | 6 | AI 1 suggestions from text and photo, never auto-applied (optional AI 1) |
| `test_web.py` | 7 | layout, navigation, badges, error pages |
| `test_demo_and_eval.py` | 2 | demo data loads twice without duplicates; evaluation runs and saves nothing |

## Lab requirements → tests

| Requirement (lab slides) | Where it is built | Tests that prove it |
|---|---|---|
| C1 sign in and roles | `access` | `test_access` (sign-in, role scope, suspended users can't sign in) |
| C2 register an asset | `catalogue` | `test_catalogue` register/edit, upload limits |
| C3 publish and search | `catalogue` | `test_catalogue` publish rules, search, filters |
| C4 request an item | `resource_requests` | `test_requests` submit/edit/cancel, idempotency |
| C5 approve and transfer | `transfers`, `blueprint.routing` | `test_approvals`, `test_transfers` (incl. two approvers racing for the last units) |
| C6 life cycle and history | `lifecycle` | `test_lifecycle`, `test_state_machines` |
| C7 sustainability dashboard, ≥ 3 measures with formula and source | `sustainability` | `test_sustainability` (5 measures, each with formula and source; unavailable ≠ 0) |
| C8 notifications | `notifications` | `test_notifications` |
| C9 report table and CSV | `reporting` | `test_reporting` (CSV = screen rows) |
| **AI 2** matching with score and reason | `matching` | `test_matching`, evaluation below |
| **AI 5** report summary, edited before publishing | `reporting`, `ai` | `test_reporting` (draft only, numbers check, AI down, adapter contract) |
| Bonus: Institution Blueprint | `blueprint` | `test_blueprint` |
| Bonus: cost-avoidance calculator | `sustainability` | `test_calculator`, `test_sustainability` (public page) |
| Bonus: Arabic / English | everywhere | `test_i18n` |
| Bonus: semantic matching | `matching` | `test_matching` (Arabic query finds English item) |
| Bonus: feasibility and net cost | `sustainability` | `test_sustainability` (`NetCostTests`) |

## Coverage

86 % of statements in `apps/` (5,111 statements, migrations and admin excluded). Highest: calculator 100 %,
reporting services 96 %, sustainability services 95 %, transfers services 92 %. Lowest: some view error branches
(`resource_requests/views.py` 67 %, `transfers/views.py` 76 %), which are mostly the non-HTMX fallbacks.
`seed_demo` is now covered by `test_demo_and_eval`.

## AI evaluation

### AI 2: matching relevance

25 labelled queries (13 English, 12 Arabic), each with the category or categories a correct answer belongs to,
run through the full Find pipeline on the demo data (`docs/evaluation/matching.md` has the per-query table):

| Queries | Hit@1 | Hit@3 | MRR | No result |
|---|---|---|---|---|
| All (25) | 100 % | 100 % | 1.00 | 0 % |
| English (13) | 100 % | 100 % | 1.00 | 0 % |
| Arabic (12) | 100 % | 100 % | 1.00 | 0 % |

**Read this carefully in the report.** The set is small and was written by the same team that wrote the
bilingual synonym table, on a catalogue of 12 published items, so it shows the pipeline works end to end in both
languages, not that it generalises. During development the same command found a real case: with the whiteboard
under maintenance, "board to write on" correctly returned nothing (hard rule), which is why the evaluation is run
on freshly seeded data. Next steps: collect 50–100 real queries from the KU pilot, label them blind, and compare
the lexical embedder with the multilingual MiniLM model (`EMBEDDING_BACKEND=sentence-transformers`).

**Speed (NFR-5, ≤ 5 s):** a Find search took 36 ms on average (10 runs), 88 ms for the first (cold) one.

**Feedback captured for tuning:** every result records the requester's decision (Request → accepted, "Not for
me" + reason → rejected) on the recommendation and the inference record.

### AI 5: report summary

What is measured automatically:
- **Invented numbers:** every number in a draft is checked against the report's totals; the editor sees the
  ones that don't match before publishing (tested with an injected "AED 9,999").
- **How much people edit:** `edit_distance_share` (0 = published as written) is stored per summary, for the pilot.
- **Graceful failure:** a timeout leaves the report working and saves no summary.

With the real model, evaluate on the pilot: share of drafts published, average edit share, and the count of
flagged numbers per draft.

### AI 1 (optional): registration suggestions

Acceptance is recorded per suggestion (fields used, or ignored). With the fake provider this is a functional
test only; accuracy needs the real model and real photos from the pilot.

## Known limitations

- The multilingual MiniLM model path is implemented but not tested in our build environment (no download).
- Real Anthropic calls are mocked in tests; they need an API key to try.
- Multi-step approvals ("Head, then Finance") are future work (one decision per request in the ERD).
- Browser tests are manual; adding Playwright to CI is the next step for regression safety.
