# Feature 2: Sustainable-action recommendations

**Module:** Sustainability (`apps/sustainability/advice.py`, views `advice_panel`, `advice_ai`) ·
**Button:** green **Sustainable actions** in the asset panel, beside Edit details and Report a problem.

## What it does

For one asset, the panel suggests the next step: keep using or reuse it, transfer it, repair or refurbish it,
donate it, take it apart for parts, recycle it, or dispose of it as the last option. Each suggestion shows:
- the reasons, in plain words;
- the other options and their trade-offs;
- labelled estimates, each with how it was worked out;
- missing information;
- the rules used.

Every option either opens an existing workflow or says **Advice only** and why.

| Screen | URL | Who |
|---|---|---|
| Advice panel (side panel, or full page from a link) | `/impact/actions/<id>/` | Custodian, or `asset.register`, `asset.custody`, `maintenance.record`, `eol.propose`, `eol.approve` or `sustainability.review` for the unit |
| Optional AI wording | `/impact/actions/<id>/ai/` (POST) | Same |

## The rules (in order; the first that applies wins)

| Situation | Recommended | Alternatives |
|---|---|---|
| Donated, recycled or disposed | None ("life cycle ended") | None |
| An end-of-life proposal is pending or approved | That proposal; let the review finish | None |
| Units reserved for a transfer | Keep: the transfer is reuse already happening | None |
| Retired, condition Fair or better | Donate | Recycle, Dispose |
| Retired, condition Poor | Recycle | Disassemble (advice only), Dispose |
| Broken (under maintenance, open record or Poor) **and** repair not worth it* | Recycle | Donate (if Fair or better), Disassemble, one more Repair, Dispose |
| Broken, repair still worth it | Repair (finish the open job or report a problem) | Recycle, Dispose |
| Registered or just transferred | Confirm condition so it can be used or offered | None |
| Available, other units waiting for this category | Transfer (publish it if it isn't listed) | Keep, Donate if older |
| Available, nobody waiting | Keep using it, or publish it | Donate if older, Transfer once published |

\* Repair is not worth it after **2 failed repairs**, or when **repairs spent + next estimated repair > 50 %
of the item's value**. The next repair of a Poor item is assumed to cost **20 % of its value**: the same
`REPAIR_SHARE_POOR` the matching score and "Reuse or buy new?" use. "Older" means **7 years or more**. "Waiting"
means requests from other units in this category (or its parent) that are pending approval and have no item
chosen yet. All of these are prototype assumptions and are listed under "How this was decided".

## Design decisions

**A1. Rule-based first, worked out on demand, never saved.** The advice is computed each time the panel opens
and nothing is written. Viewing it cannot change the asset, start a workflow or approve anything (the test
checks `row_version`, history and proposals before and after). The design's `SustainabilityRecommendation`
entity (Figure 7.11) records accept/reject decisions on AI advice. It needs a `ModelVersion` and is left for
AI feature 3. *Why:* the brief says "never let a recommendation automatically change the asset state", and a
stored rule result would go stale as soon as the asset changes.

**A2. Links only where the workflow would accept the step.** "Propose this" appears only if the person has
`eol.propose`, no proposal is open, no units are reserved and the state allows it. These are the same guards
as `propose_end_of_life`, which still checks again on the server. "Report a problem" follows the same pattern.
Otherwise the option says why there is no button ("Your role can't start this", "Units are reserved…"). The
proposal form opens with the suggested action pre-selected, and the person can still change it.

**A3. Disassembly is advice only.** The system has no workflow or end state for taking an item apart. The option
says so and suggests proposing Recycle with the kept parts listed in the reason.

**A4. Estimates reuse existing formulas and are labelled.** The figures shown are:
- **Buying one new**: the estimated value.
- **Saved if one unit is reused instead**: value minus the AED 40 / 120 transfer cost, the same formula as
  `record_transfer_impact`, shown as a range.
- **Next repair (assumed)**: 20 % of the value.
- **Repairs recorded**: the sum of repair records.
- **Carbon of making one new**: the locally selected carbon factor, with its source and date.

A missing input means no figure, and a line under **Missing information** instead. Nothing is added up into
a total, so the same benefit is never counted twice.

**A5. Optional AI wording, clearly labelled.** "Ask AI to explain this" sends the facts, the rule result and the
estimates (no names of people) through `AIGateway.recommend_action`. The reply is shown only if every number
in it appears in what was sent. It carries a label: **Written by an AI model (name)**, or **Offline stand-in,
not a real AI model** for the fake provider. With the default offline provider, or if the model is down, the
page says AI is unavailable and that the rule-based explanation stands. A `RECOMMEND` model version is now seeded.

**A6. The button.** `.btn-green` uses `--ok` (#17703F) with white text, a 6.1:1 contrast that passes WCAG AA.
The hover colour is darker and focus gets a visible outline. Size, radius and spacing come from `.btn`. The
sprout icon comes before the text: on the left in English and on the right in Arabic, as the reading
direction expects. The button sits in the same wrapping `.actions` row, so it reflows on phones.

**A7. Found while building:** "Reuse or buy new?" (`/impact/compare/<id>/`) didn't check whether the person may
view the asset. It now applies `can_view`.

## Tests

`tests/test_advice.py` covers:
- every branch of the rules;
- links that depend on permission and state;
- missing information;
- the carbon source;
- read-only viewing;
- access: requesters get 404, including the AI endpoint;
- the green button shows only to advisers;
- the full page and the Arabic page;
- the pre-selected proposal action;
- the AI cases: fallback, labels, invented numbers dropped, no names sent.
