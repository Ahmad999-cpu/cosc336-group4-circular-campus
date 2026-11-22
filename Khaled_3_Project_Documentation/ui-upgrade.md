# UI upgrade (after validation): brighter, more interactive, more polished

The palette stays exactly as approved: navy `#0E1F3A`, light blue `#D6E3F1` / `#7EA6CE`, scarlet `#E5323B`.
Everything is in `static/css/theme.css` (tokens at the top, then a clearly marked "UI v2" layer at the end),
plus a few lines in `static/js/app.js` and `templates/base.html`. No screen had to change its markup.

## What changed

| Area | Before | Now |
|---|---|---|
| Ground | cool grey `#F2F5F9` | near-white `#F6F9FD`, so white panels and the colours read brighter |
| **Page band (the one bold element)** | title on the plain ground | every page opens on a full-width light-blue band; the reuse loop (two arrows chasing each other, the brand idea) is drawn large behind the title and turns into place on load; a short scarlet bar underlines the title |
| Panels and cards | flat border | soft blue-tinted shadows; cards, matches, requests and routes lift on hover; item art has a light radial glow |
| Tiles | flat | each measure gets a coloured top edge (light blue / scarlet / navy); the hero tile has a navy glow; summary cards get a coloured side edge |
| Buttons | colour change on hover | lift on hover, press on click, scarlet buttons get a subtle gradient and glow; **a spinner replaces the label while an action runs**, so a double click can't happen and the person sees it working |
| Progress | none | a thin scarlet line sweeps across the top of the page while any action is running (only if it takes longer than 0.12 s; background refreshes never show it) |
| Tables | white header | light-blue header and row hover |
| Inputs | — | brighter focus ring and hover border |
| Toasts | plain | a timer line shows when the toast will disappear |
| **Celebration** | — | confirming a receipt (the moment an item is actually reused) shows a special toast with a small burst in the brand colours |
| Empty states | text only | the reuse loop icon (blue and scarlet) above the message |
| Lists | appear at once | cards, matches and requests arrive in a short stagger on first paint |
| Drawer | — | light-blue head, deeper shadow, slightly blurred page behind |

## Design decisions

**D1. Spend the boldness in one place.** The light-blue band with the loop is the identity of every screen; the
navy hero stays only on Home and Find, where the main ask lives. Everything else got quieter but crisper.

**D2. Motion only answers something.** Hover lift, button press, spinner, progress line, toasts, stagger on
first paint, and one celebration — when an item is really reused. No looping decoration.

**D3. Accessibility kept.** All motion is switched off with `prefers-reduced-motion`; focus rings are thicker;
colours keep the contrast checked in Step 1 (white on scarlet button fill 5.3:1). The validation scan was re-run
after the upgrade: 0 issues on 17 pages at desktop and phone widths, and the 37-check walk-through still passes.

**D4. Right-to-left.** Every new rule uses logical properties (`inset-inline-*`, `margin-inline`), the loop
mirrors to the left in Arabic, and the progress sweep runs right-to-left.

## Files

`static/css/theme.css` (tokens and the UI v2 layer), `static/js/app.js` (progress line, celebration burst,
toast timer), `templates/base.html` (progress element), `apps/web/templatetags/ui.py` (a message can ask for a
celebration), `apps/transfers/views.py` (receipt asks for it).
