# Module: Shared front end (`apps/web`, `templates/`, `static/`)

**Delivers:** the look, layout and shared behaviour every screen uses: base template, design system,
UI template tags, HTMX helpers, the home page, the `runworker` and `seed_demo` commands.
**Brief:** "user-centered interfaces, dashboard layouts, accessibility considerations" (Objective 4);
"Design and implement the user interface" (Phase 6 slides).
**Owns no tables.**

## What is in it

| File | What it is |
|---|---|
| `templates/base.html` | Top bar (brand, menu, signed-in person and roles, language switch, notification bell, sign out), main area, side panel, toast area |
| `static/css/theme.css` | The design system: colour and type tokens, then every component (buttons, panels, pills, match rows, score ring, cards, side panel, tables, tiles, forms, toasts) |
| `static/js/app.js` | Toasts, button ripple, disclosures, side panel open/close with focus trap, notification popover, quantity steppers, score-ring and counter animation, scroll reveals, HTMX glue |
| `static/vendor/htmx-2.0.4.min.js` | HTMX, shipped with the code so the lab works without internet |
| `apps/web/templatetags/ui.py` | `{% icon %}`, `{% ring %}`, `{% pill %}`, `{% steps %}`, `{% empty_state %}`, `{% flash_messages %}`, filters `aed` and `num` |
| `apps/web/htmx.py` | `is_htmx`, `with_toast` (toast + close panel after an HTMX post), `redirect_htmx` |
| `apps/web/navigation.py` | The menu: one line per screen with its permission and badge count |
| `apps/web/context.py` | Puts the menu, roles and notifications on every page |
| `templates/components/` | `empty.html` (empty state), `drawer_head.html` (side panel header) |

## Design decisions

**D1. Server-rendered pages with HTMX, no frontend framework.**
Pages are Django templates; HTMX swaps fragments for filters, side panels and inline approvals. *Why:* one
codebase in one language, classes stay the ones in the class diagram, and every rule is enforced on the
server (C1 "hiding a button is not enough"). React would have meant a second application and an API layer
for a three-week build. *Traces to:* ADR-1 (one deployable), NFR-23 (separation of UI, logic, data).

**D2. Our own design system instead of Bootstrap.** *(changes the Implementation Plan, which listed Bootstrap)*
The approved prototype was built without Bootstrap, and mixing the two would fight over spacing, buttons and
forms. `theme.css` is about 400 lines: tokens first, then components. *Why:* the team approved that exact
look; one stylesheet keeps every screen consistent; logical CSS properties (`inset-inline-start`) make the
Arabic right-to-left layout work without a second stylesheet. Recorded as B8 in `docs/design-changes.md`.

**D3. The palette and type are tokens.** Navy #0E1F3A, light blue #7EA6CE / #D6E3F1, scarlet #E5323B with a
darker button fill #D0222C (white text passes 5.3:1 contrast; #E5323B would only reach 4.3:1). Anton for
headlines, Archivo for text, IBM Plex Sans Arabic in Arabic. *Why:* one place to change; contrast meets WCAG
AA (the brief's accessibility requirement).

**D4. Red means "the next action".** Only the primary button of a screen, the active-menu underline and
urgent counts are red. Everything else is navy or grey. *Why:* visual hierarchy: a user always sees the one
thing to do next.

**D5. Motion answers actions.** Side panels slide, rings fill, steps fill, counters count up, toasts appear.
The one page-load moment is the headline on the home page. Everything is switched off when the device asks
for reduced motion. Content is visible before any animation runs. *Why:* usability without distraction;
accessibility.

**D6. The menu follows permissions.** `navigation.py` lists every screen with the permission needed
anywhere (`has_any`); a screen whose module is not built yet is skipped. *Why:* each person sees only their
work; the menu grows as modules land, with no edits to the base template. The services still check the real
permission for the real department (C1).

**D7. Feedback for every action.** Django messages and HTMX responses become toasts (`with_toast`), with an
optional link ("View"). A failed HTMX request shows a plain error toast. *Why:* "immediate visual feedback for
user actions".

**D8. Accessible by construction.** Skip link, real buttons and links, labels on every input, visible focus,
`aria-live` toasts, `aria-expanded` on disclosures and the bell, focus kept inside an open side panel, Esc
closes it. *Why:* the brief's accessibility requirement; NFR on usability.

**D9. Missing numbers show as "unavailable", never 0.** The `aed` and `num` filters enforce it. *Why:*
FR-13.8, FR-15.10.

## Added to another module

- `apps/access/permissions.py` gains `has_any(user, action)`: "may this person do this anywhere", used only
  to decide what to show.

## How other modules use it

```django
{% extends "base.html" %}{% load i18n ui %}
{% block content %}<section class="page">
  <div class="page-head"><div><h1>{% translate "Approvals" %}</h1><p>…</p></div></div>
  {% ring match.score %} {{ asset.estimated_value|aed }} {% pill "ok" _("Suitable") %}
</section>{% endblock %}
```
Side panel: `<button hx-get="{% url 'catalogue:panel' asset.pk %}" hx-target="#drawer">`, and the fragment
starts with `{% include "components/drawer_head.html" with title=asset.name %}`.

## Tests (`tests/test_web.py`)

Ring targets its score; weak scores use the warning colour; `aed` shows "unavailable" for missing values and
formats AED; request steps mark done/current; home needs sign-in; home renders; Arabic switches to
right-to-left.

## Left for later steps

Each module adds its own screens and its line in `navigation.py`. Arabic translations of all strings come in
step 12.
