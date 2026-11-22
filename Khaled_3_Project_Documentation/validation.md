# Validation loop (after all steps, before the UI upgrade)

Goal: check that every part works with every other part, as each role, in both languages, and fix what breaks.
Run on 14 Nov 2026 against a freshly seeded database.

## What was run

| Check | How | Result after fixes |
|---|---|---|
| Unit, service and screen tests | `python manage.py test` | 192 tests pass |
| **Crawl** | as each of the 10 demo users, in English and Arabic: open the start page and follow every link and `hx-get` up to three hops (932 page loads); flag any 5xx, unexpected 404, or an Arabic page that isn't right-to-left | 0 problems |
| **Cross-role walk-through** in a real browser (Playwright) | club finds and requests → approver approves (badge drops live) → facilities dispatches → club confirms receipt with "replaced a planned purchase" → Impact counts it and shows it as verified → notifications arrive → sustainability officer sees it in Reports, drafts and publishes the AI summary → custodian sees the move in the history and reports a problem → technician starts work (badge) → Arabic Find with an Arabic query → admin adds a Blueprint route and tests it → approver rejects with a reason → requester reads the reason | 37 of 37 checks pass, no browser console errors, no 5xx |
| **Accessibility and layout** | on 17 key pages, desktop (1366 px) and phone (390 px): duplicate ids, inputs without a label, buttons/links without a name, images without alt, horizontal overflow | 0 issues |
| Static checks | `pyflakes`, `makemigrations --check`, `check --deploy`, search for `|safe` / `mark_safe` | clean (deploy warnings only appear with `DJANGO_DEBUG=1`) |
| Translations | `test_i18n` | every entry translated |
| Matching quality | `evaluate_matching` | see `docs/phase7-testing.md` |

## Bugs found and fixed

| # | Found by | Problem | Fix |
|---|---|---|---|
| 1 | crawl | Maintenance staff opening an item under repair from the Maintenance board got a 404 (only published items, custodians and registrars could see unpublished items) | `catalogue.services.can_view`: people who register, maintain, approve or dispatch for the owning unit can open its unpublished items; used by the item panel and the history page. Test added. |
| 2 | review of the session rules | The one-minute badge refresh (Step 9) and the approvals queue auto-refresh counted as activity, so an idle session never reached the 15-minute limit (NFR-17) | Automatic refreshes send `X-Background: 1`; the session middleware only renews the session on real activity (`SESSION_SAVE_EVERY_REQUEST` off). Test added. |
| 3 | edge-case review | After the session timed out, a click inside a side panel loaded the sign-in form *inside* the panel; a 403 showed the error page inside a table cell; an expired CSRF token showed a bare 403 | `HtmxEdgeMiddleware`: signed out → whole page goes to sign-in and comes back (`next`); 403 → a toast; stale CSRF → the page reloads. Tests added. |
| 4 | layout scan | Impact page scrolled sideways on a phone | Screen-reader labels inside table cells were positioned against the page; `.queue` tables now contain them. |
| 5 | Arabic walk-through | "3 minutes ago" read as "3 دقائق مضى" (word order) on three boards | Use the translated "%(t)s ago" sentence ("منذ 3 دقائق"). |
| 6 | Arabic walk-through | Ten error messages were built with f-strings ("Only 2 unit(s) free"), so they stayed English in Arabic | Rewritten as translatable sentences with placeholders; translated. |
| 7 | walk-through | Offline AI summary said "1 requests" | Singular/plural in the offline provider. |
| 8 | `check --deploy` | Production settings relied on people remembering them | With `DJANGO_DEBUG=0`: refuses the development secret key, redirects to HTTPS, HSTS, secure cookies. |
| 9 | evaluation | "Board to write on" found nothing on the long-running dev database | Not a bug (the whiteboard was under maintenance, a hard rule); the evaluation is now documented to run on freshly seeded data. |

Earlier fixes made while building (each listed in its module doc): transfer ordering by reservation time
(Step 8), partial-page detection from `HX-Target` instead of `?partial=1` in the address bar (Step 8), score
rings not animating inside replaced content (Step 7), approvals badge not refreshing (Step 9).

## How to repeat it

```bash
python manage.py flush --no-input && python manage.py seed_demo
python manage.py test
python manage.py shell < tools/crawl.py          # every link, every role, both languages
python manage.py runserver                       # in another terminal, then:
pip install playwright && playwright install chromium
python tools/e2e_walkthrough.py                  # the 37-check cross-role walk-through (re-seed before each run)
python tools/a11y_scan.py                        # labels, names, duplicate ids, phone overflow
```
