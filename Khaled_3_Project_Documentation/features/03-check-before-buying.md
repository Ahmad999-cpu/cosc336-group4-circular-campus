# Feature 3: Check before buying

**Module:** Matching (`apps/matching/procurement.py`, view `procure`) · **URL:** `/find/before-buying/`, linked from Find ·
**Who:** `request.submit` or `request.approve` (only `request.submit` gets the Request button).

## What it does

The form asks for:
- a description (required);
- category, quantity, must-have specifications and the lowest acceptable condition;
- delivery campus and a needed-by date;
- an optional estimated purchase price per unit.

The page then lists published items from other units that could replace the purchase. Each card shows:
- name, unit, location, condition and free units;
- the match score and its one-line reason;
- the reasons the match is only partial;
- the cost of buying new, the transfer and repair cost instead, and the estimated purchase cost avoided;
- "How this was worked out";
- **Request N units**, which opens the normal request form pre-filled. Nothing is sent until the person submits it.

A summary at the top says how many of the units reuse could cover, from which items, how many would still
need buying, and the estimated money not spent, with each unit counted once.

## Design decisions

**P1. One matching system.** The check calls the existing `services._run` (hard rules, embeddings, eight factors,
explanations, keyword fallback). The only addition is an `allow_partial` flag. With it, the hard rule needs at
least one free unit instead of the full quantity, and factor f8 becomes `free / needed` with the note "only N of
M free". Find and request matching don't pass the flag, so they behave exactly as before. The search is logged
as a `MatchResultSet`, like every Find search.

**P2. One savings formula.** Each card uses `sustainability.services.net_cost_comparison`, the function behind
"Reuse or buy new?": new price × units − (transfer + storage + repair). The new price is the person's
estimated price if they gave one, otherwise the item's estimated value, and the card says which.

**P3. No double counting.** The cards are alternatives, so their savings are never added up. The summary takes the
suitable items in score order until the quantity is covered, and counts each unit once. It skips weak matches,
items that aren't possible and items that cost more than buying new. If any item in that combination has no
value, no total is shown. Weak matches show no money figure at all.

**P4. Partial matches are explained.** The card says so when fewer units are free than needed. When
specifications were given, it says whether only some appear in the listing, or that they appear but nobody has
checked them on the item. The engine's own notes (different size, other campus, value unknown…) stay in the
reason line.

**P5. Nothing automatic.** The page never submits a request, reserves units or approves anything. A test checks
that the request count and reserved quantity are unchanged. The Request button carries the asset, the
quantity it can cover (never more than is free) and the match id. The request service still checks
everything again.

**P6. Visibility.** Only published items from other units appear, the same rule as Find. The item details and
"Reuse or buy new?" panels now check `can_view` too (see Feature 2, A7).

**P7. Arabic.** The form fields use `dir="auto"`, so English typed on an Arabic page isn't scrambled.

## Tests

`tests/test_procurement.py` covers:
- the shared formula figures;
- partial quantity;
- specification wording;
- your price versus the item's value;
- counting each unit once;
- no matches;
- the own-unit and unpublished exclusions;
- the page never requests or reserves;
- permissions and validation;
- the keyword fallback;
- the screens for requester, approver and custodian, signed out, and invalid input.
