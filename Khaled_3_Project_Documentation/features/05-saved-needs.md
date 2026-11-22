# Phase 5: Saved needs (wishlist) and availability alerts

**Module:** Matching (`apps/matching/wishlist.py`, models `SavedNeed`, `NeedMatch`, receiver `check_saved_needs`) ·
**URL:** `/find/saved/` · **Menu:** Saved needs · **Who:** `request.submit`. Each person sees only their own needs.

## What it does

A person saves a need: a description or purpose, category, quantity, desired specifications and lowest
condition, preferred campus and an optional needed-by date. Anything that already fits is listed straight away.
After that, whenever an item is **published** or a published item **gets free units again** (a reservation is
released, quantity is corrected, it comes back from maintenance), the active needs are scored against it. A
suitable match (score 70 or above) sends a notification in English and Arabic, in-app and by e-mail. The
notification links to the item, where **Request this** opens the normal request form. The need page shows every
current match, labelled as weak or partial ("Covers 1 of 2") where that applies, with the engine's explanation,
**Details** and **Request**. People can edit, deactivate, re-activate, check now and delete their needs.

## Design decisions

**W1. Same matching as Find.** Candidates pass the same hard rules (published, other units, category subtree)
except quantity: at least one free unit is enough, and a partial match is shown as partial. Each candidate is
scored by `MatchingEngine.factors` and `rank` with the same embedder and carbon factors. There is no second
scoring system.

**W2. When it runs.** It listens to the existing `asset_history` signal (publication, release, state change,
quantity or condition update) and runs **after the transaction commits** (`on_commit`). Publishing is never
slowed down or undone by the check. Reservations never trigger a check, because they take units away.

**W3. No repeated alerts.** `NeedMatch` keeps one row per need and item. Its `signature` records what the person
was told: units covered, condition and score band (tens). An alert is sent only when the signature differs from
the one last notified. Unpublishing and republishing the same item doesn't alert again. More units becoming
free (partial to full) does, because the match changed. Items that already fit when the need is saved are shown
on screen and counted as told.

**W4. Never reserves.** Alerts and the page only link to the item and to the request form. Tests check that
requests and `reserved_quantity` are unchanged.

**W5. Privacy.** Only the owner can list, edit or delete a need. Anyone else gets 404, and the service raises
`Forbidden`. Only published items appear in matches.

**W6. When matching is down.** If the embedder fails, the need is kept and flagged. The page says matching was
unavailable, and the custodian's publish still succeeds. "Check now" tries again.

**W7. Limits.** Each person can have up to 20 active needs. The description must be 3–300 characters, the
quantity 1–999, and the needed-by date can't be in the past. Once the date passes, the page suggests editing or
deleting the need.

**W8. New notification types** `NEED_MATCH`, `AVAILABILITY`, `ASSET_QUESTION` and `ASSET_ANSWER` (one migration
in Notifications). The last three are used by Phases 6 and 7.

## Tests

`tests/test_wishlist.py` covers:
- an alert on publication, stored in both languages, with an item link and no request or reservation;
- no repeat for an unchanged match, and a re-alert when the match changes (partial to full);
- existing matches shown but not notified;
- unrelated items and the person's own unit excluded;
- inactive needs ignored;
- owner-only access;
- validation;
- edit re-check and delete;
- matching down;
- the screens and actions, and the permission check.
