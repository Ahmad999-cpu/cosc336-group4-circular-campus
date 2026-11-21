# Circular Campus — instructions for Claude Code (and for us)

Everyone on the team runs Claude Code in this repo. This file keeps the four of us building one
system, not four. Read it before you prompt. If you change a convention, change it here in the same commit.

## What this is

COSC 336 Group 4 project: an AI-powered circular campus resource-exchange and asset life-cycle system.
The same code is the prototype for the Circular Campus pilot at KU.

The design is in our Phase 4 & 5 document (class diagram Figure 5.1, state machines Figures 7.5–7.11,
component diagram Figure 7.12, ADR-1 to ADR-5, Tables 9.1–9.5). **Code follows the design. When the code has to
differ, write it down in `docs/design-changes.md` and in the module's doc.**

Stack: Django 5.1, PostgreSQL 16 + pgvector, server-rendered templates with our own design system
(`static/css/theme.css`, `static/js/app.js`, `{% load ui %}` tags) and HTMX for partial updates,
a polling worker (`manage.py runworker`). Python 3.12+.

## Commands

```bash
docker compose up -d                 # Postgres + pgvector on port 5432
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # add requirements-ai.txt when you work on AI
cp .env.example .env
python manage.py migrate
python manage.py seed_demo           # demo users, password demo-pass-2026
python manage.py runserver           # http://localhost:8000
python manage.py runworker           # second terminal: e-mail outbox + embeddings
python manage.py test                # must pass before every push
```

## Architecture rules (do not break these)

1. **One Django app per module** (`apps/<module>`), matching the component diagram. A module owns its
   tables. Another module may read them in queries, but **writes only through that module's
   `services.py` or entity methods**. Never write to another module's table directly.
2. **Calls go down only.** Order, lowest first: `access, audit, notifications, ai, catalogue, blueprint,
   resource_requests, transfers, lifecycle, sustainability, matching, reporting, web`. A module never
   imports a module above it. When a lower module needs to tell a higher one something, it uses a signal
   (see `catalogue/signals.py`).
3. **Views are thin.** A view parses the form, calls one service function, and renders the result. Business
   rules live in services and entity methods, never in views or templates.
4. **Every service that changes data starts with `require(user, "<permission>", department)`**
   (`apps/access/permissions.py`). Hiding a button is not a permission check (C1).
5. **States change only through entity operations** (`asset.allocate`, `request.approve`,
   `transfer.dispatch`…), which use `common.statemachine.move`. Never set a `status`/`lifecycle_state`
   field directly, and never add a state field to a form.
6. **Anything that changes quantities or custody runs in `transaction.atomic()` with
   `select_for_update()` on the rows it changes.** Copy the pattern in `transfers/services.approve_request`.
7. **History is append-only.** Asset operations emit `asset_history`; Life Cycle writes the event. Never
   update or delete `LifeCycleEvent`, `AuditLog`, `DeliveryEvent`; add a correction row instead.
8. **No hard-coded roles.** Check permission codes (`asset.publish`, `request.approve`…) from
   `access.models.PERMISSIONS`. Role names, units and approval limits are data (Institution Blueprint).
   Add a new permission code to `PERMISSIONS` and to a new data migration in `access`.
9. **AI is advisory and goes through `apps/ai/gateway.py` only.** No module imports a provider SDK. AI code
   never writes business tables (BR-12); a person accepts, edits or rejects, and the normal service saves.
   Every AI call returns an `AIResult`; handle every status, including `UNAVAILABLE` and `TIMEOUT`, with the
   conventional fallback (NFR-26).
10. **Numbers come from deterministic code.** Totals, scores and savings are computed in Python/SQL. The AI
    may describe numbers, never produce them.
11. **Every user-facing string is translatable**: `gettext_lazy as _` in Python, `{% translate %}` in
    templates. Layouts must work right-to-left: use logical CSS (`inset-inline-start`, `margin-inline-end`),
    never `left`/`right`.

## Code conventions

- Class and method names follow the class diagram, in Python style: `isPublishable()` → `is_publishable()`,
  `ResourceRequest.selectAsset` → `select_asset`.
- Errors: raise a subclass of `common.errors.DomainError` with a code from Table 9.1
  (`SELF_APPROVAL`, `INSUFFICIENT_QUANTITY`, `NOT_PENDING`, `CONFLICT`…). Views turn them into messages.
- Money is `DecimalField` in AED. Never `float` for money.
- Missing data stays `None` and is shown as "unavailable", never as 0 (FR-13.8, FR-15.10).
- Templates go in `apps/<module>/templates/<module>/`. Extend `base.html`. Use the classes and CSS variables in
  `static/css/theme.css` (see `docs/modules/web.md` for the component list); don't hard-code colours, and don't
  add another CSS framework.
- Side panels: a button with `hx-get="<url>" hx-target="#drawer"` loads a fragment that starts with
  `{% include "components/drawer_head.html" %}`; app.js slides it in. Answer HTMX posts with
  `apps.web.htmx.with_toast(...)` for feedback.
- URLs are namespaced: `{% url 'catalogue:search' %}`. Add your screen to `NAV` in `apps/web/navigation.py`.

## Arabic and messages

- Every user-facing string: `{% translate %}` / `{% blocktranslate %}` in templates, `gettext` in views.
- Services may raise `ValidationFailed("Plain English sentence")`: our `makemessages` collects these, and the
  middleware translates them when shown. Don't build these messages with f-strings, or they can't be translated.
- Notifications: `enqueue(user, type, Msg(_l("… %(name)s …"), name=...))` so they are stored in both languages.
- After changing text: `makemessages -l ar`, translate, `compilemessages -l ar`. `tests/test_i18n.py` checks it.
- Partial-page views decide "partial or full page" from the `HX-Target` header, not from a query parameter.

## Wording rules (the pitch depends on these)

- Carbon factors are "locally selected carbon factors" with a source and date. Never write
  "official UAE carbon factors".
- Label every estimate as an estimate. Keep verified avoided purchases separate from estimated savings.

## Team workflow

- Work only in your own module unless you've agreed otherwise. Owners are listed in `docs/README.md`.
- Branch per feature, small commits **under your own name**, push at least every working session. The
  commit history is graded for individual authorship.
- Write the test for a rule before the code for it (see `tests/`). `python manage.py test` must pass before
  you push.
- When you make a design decision, add it to your module's doc in `docs/modules/` in the same commit.
- Migrations: run `makemigrations <your_app>` only for your own app. If you need a field in someone else's
  model, ask them; they add it.
- Don't commit `.env`, API keys, real KU data, or personal data.

## Definition of done for a feature

Permission checked on the server · state changes only via entity operations · history/audit written ·
works in Arabic and English · AI-down fallback works · tests for its rules pass · module doc updated.
