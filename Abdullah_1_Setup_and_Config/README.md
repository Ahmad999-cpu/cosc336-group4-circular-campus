# Circular Campus

AI-powered circular campus resource exchange and asset life-cycle management — COSC 336, Group 4, Fall 2026.

## Run it

```bash
docker compose up -d                       # PostgreSQL 16 + pgvector
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo                 # demo users; password: demo-pass-2026
python manage.py runserver                 # http://localhost:8000
python manage.py runworker                 # in a second terminal
python manage.py test
```

Demo logins (password `demo-pass-2026`, or the one-click buttons on the sign-in page while `DJANGO_DEBUG=1`):

| Who | E-mail | Sees |
|---|---|---|
| Omar, club president | `club@demo.local` | Find, Browse, Saved needs, My requests, Impact |
| Rana, requester | `requester@demo.local` | Find, Browse, Saved needs, My requests, Impact |
| Cara, custodian (Engineering) | `custodian@demo.local` | Our assets, Maintenance |
| Lina, custodian (Library, Science) | `lina@demo.local` | Our assets, Maintenance |
| Adam, approver (Engineering, up to AED 2,000) | `approver@demo.local` | Approvals, Reports, Demand |
| Dana, dean (whole institution) | `dean@demo.local` | Approvals, Reports |
| Faisal, facilities | `facilities@demo.local` | Transfers |
| Tariq, maintenance | `tech@demo.local` | Maintenance |
| Sara, sustainability officer | `sustain@demo.local` | Impact, Reports (publishes AI summaries), Demand |
| Ali, system administrator | `admin@demo.local` | People, Setup (Institution Blueprint), Reports, Demand |

Developer admin site: `/admin/` as `dev@demo.local`. Public page without sign-in: `/impact/calculator/`.

## Optional settings (`.env`)

| Setting | Default | What it does |
|---|---|---|
| `AI_PROVIDER` | `fake` | `anthropic` uses the real model for the report summary (AI 5), Blueprint drafts and registration suggestions (AI 1); set `ANTHROPIC_API_KEY` too and `pip install -r requirements-ai.txt` |
| `ANTHROPIC_MODEL` | `claude-haiku-5-5` | Model used when `AI_PROVIDER=anthropic` |
| `EMBEDDING_BACKEND` | `lexical` | Matching (AI 2). `sentence-transformers` uses the multilingual MiniLM model (needs `requirements-ai.txt` and a one-time download) |
| `SITE_BASE_URL` | empty | Address printed in asset QR labels, e.g. `https://circular.example.edu` (for a phone demo on the same Wi-Fi: `http://<laptop-IP>:8000`, add that IP to `DJANGO_ALLOWED_HOSTS` and run `runserver 0.0.0.0:8000`). Empty = the address you opened the site with |
| `DJANGO_DEBUG` | `1` | `0` for the pilot: HTTPS only, secure cookies, and a real `DJANGO_SECRET_KEY` is required |

## Features added in November 2026 (eight)

| # | Feature | Where | Who | Design notes |
|---|---|---|---|---|
| 1 | QR labels for assets | Asset panel → **QR label** (`/assets/<id>/qr/`) | Custodian, asset managers, maintenance | `docs/features/01-qr-codes.md` |
| 2 | Sustainable-action recommendations | Green **Sustainable actions** button in the asset panel | Custodian, maintenance, end-of-life reviewers, sustainability officer | `docs/features/02-sustainable-actions.md` |
| 3 | Check before buying | Find → **Check before buying** (`/find/before-buying/`) | Requesters, approvers | `docs/features/03-check-before-buying.md` |
| 4 | Demand forecast | **Demand** menu (`/reports/demand/`) | `reports.view` | `docs/features/04-demand-forecast.md` |
| 5 | Saved needs and availability alerts | **Saved needs** menu (`/find/saved/`) | Requesters | `docs/features/05-saved-needs.md` |
| 6 | Coming-soon (future-available) items | Asset panel → **List as coming soon**; Browse → Coming soon | Custodians list; everyone sees | `docs/features/06-coming-soon.md` |
| 7 | Questions on an asset | Asset panel → Questions; `/assets/questions/` | Anyone who can view the item asks; custodian answers | `docs/features/07-asset-questions.md` |
| 8 | Bulk CSV upload | Our assets → **Import from CSV** (`/assets/import/`) | `asset.register`, own units only | `docs/features/08-bulk-import.md` |

New dependency: `segno` (QR codes, pure Python). New migrations: `catalogue 0003–0005`, `matching 0003`,
`notifications 0003`. After pulling: `pip install -r requirements.txt && python manage.py migrate && python manage.py seed_demo`.
The demo seed adds ten mesh office chairs listed as coming soon from 1 Jan 2027. The demand forecast has a
**Show sample data (demo)** switch that generates a labelled sample in memory (never stored).

## Public guest site

Visitors who are not signed in now land on a public site: Home (`/`), How it works (`/how-it-works/`) and Contact
(`/contact/`), with Sign in linking to the existing sign-in page (unchanged). Settings, e-mail setup and image notes:
`docs/features/guest-site.md`. Run `python manage.py migrate` once (adds `guest 0001`).

## Arabic

Translations live in `locale/ar/LC_MESSAGES/django.po` (compiled `.mo` is committed). After changing any
user-facing text: `python manage.py makemessages -l ar --ignore "staticfiles/*" --ignore "tests/*"`, translate
the new entries, then `python manage.py compilemessages -l ar` (needs GNU gettext). `tests/test_i18n.py` fails
if anything is left untranslated.

## Phase 7 helpers

```bash
python manage.py evaluate_matching          # matching relevance on labelled English and Arabic queries
coverage run --source=apps manage.py test && coverage report
```

## Where things are

| Path | What |
|---|---|
| `apps/<module>/models.py` | The classes of the Phase 5 class diagram, with their operations and state machines |
| `apps/<module>/services.py` | The module's public functions; views call these |
| `apps/ai/gateway.py` | The only way to call an AI provider |
| `apps/common/` | Shared base model, enums, errors, state-machine helper |
| `tests/` | Tests for the business rules |
| `docs/` | Design decisions per module (`docs/modules/`), changes from the design document, Phase 7 testing and evaluation |
| `CLAUDE.md` | Rules for everyone (and for Claude Code) working in this repo |
