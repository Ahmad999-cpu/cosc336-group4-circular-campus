# Phase 6: Future-available ("coming soon") items

**Modules:** Catalogue (`Asset.expected_available_on`, `upcoming_note`, `set_expected_date`, `cancel_expected_date`,
`upcoming()`) and Matching (interest via `SavedNeed.asset`, `express_interest`, `availability_changed`) ·
**Migration:** `catalogue 0003_expected_availability`

## What it does

A custodian with `asset.publish` for the unit opens an item that isn't in the marketplace. They click **List as
coming soon**, then set a date and an optional note, for example "Ten office chairs, free after the office refit,
from 1 Jan". The listing works like this:

- **Browse** shows a separate **Coming soon** section with dashed cards that say "From 1 Jan" and "10 coming",
  apart from the items available now.
- The item panel says **Coming soon: expected from …**, or **date passed** once the date has gone. It shows no
  Request button.
- Requesters can press **Tell me when it's ready**. That is interest only, not a reservation.
- When the custodian **confirms the condition and publishes** the item, the coming-soon listing ends and everyone
  who asked gets "*X* is now available".
- If the date is **changed**, everyone who asked is told the new and old dates.
- If the listing is **cancelled**, they're told and their interest is closed.
- The custodian's console shows "Coming soon: date", and "date passed" in red when overdue.

## Design decisions

**U1. A date, not a state.** The asset state machine (Figure 7.5) is unchanged. A coming-soon item keeps its real
state: Registered, Available but unpublished, Under maintenance or Transferred. It just has an expected date.
`is_upcoming` requires a date, not being published, and one of those states. Items at the end of their life
can't be listed.

**U2. The date guarantees nothing.** Only publication makes an item requestable. `submit_request` already refuses
unpublished items, and a test confirms it for coming-soon items. The panel, the form and the alerts all say
that the custodian must confirm the item is ready. Overdue dates stay visible as "date passed" and are never
treated as available.

**U3. Interest reuses saved needs.** "Tell me when it's ready" creates a `SavedNeed` tied to the asset (one per
person and item). The Phase 5 publication check notifies interest needs when their own item is published,
whatever the score, and the duplicate protection stops a second alert. The Saved needs page lists interests
separately, with **Stop telling me**.

**U4. Changes are told through the existing signal.** `set_expected` and `clear_expected` write history
("Expected available from …", "Coming-soon listing cancelled") through `asset_history`, with an `availability`
detail. Matching listens and notifies after commit. Catalogue never imports Matching (rule 2).

**U5. Visibility.** A coming-soon listing is meant to be found, so `can_view` lets everyone signed in open it.
Only `asset.publish` for the unit can set, change or cancel the date. Each of those changes is audited.

**U6. Demo data.** `seed_demo` adds "Office chair, mesh back" (10 units, Mechanical Engineering), expected from
1 Jan 2027.

**Limitation.** Find and "Check before buying" rank only items that are available now. Coming-soon items are
found in Browse and through saved needs.

## Tests

`tests/test_upcoming.py` covers:
- listing an item and the history it writes;
- the rules: permission, a future date only, not already published, not end-of-life;
- no request is possible;
- discovery in Browse and the panel, with no Request button;
- interest is not a reservation, and the alert when the item is ready;
- date change and cancellation alerts;
- overdue display;
- the interest rules;
- the custodian and requester screens.
