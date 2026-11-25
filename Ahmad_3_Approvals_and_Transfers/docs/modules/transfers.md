# Module: Approvals & Transfers (`apps/transfers`)

**Delivers:** C5 approve and transfer · Features 4.7 and 4.8 (UC-30, UC-32 to UC-38) · BR-5, BR-6, BR-7, BR-8,
BR-9, BR-13
**Lab slide C5:** "Have at least one approval step, with no self-approval. The receiver confirms; owner and
department change. The last item cannot go to two people."
**Brief:** "approval workflows for asset release, reservation, transfer, receipt"; "transfer-management
functions that record approval, collection or delivery arrangements, custody changes, new location, transfer
confirmation".
**Owns:** `ApprovalDecision`, `Transfer`, `DeliveryEvent`

## Screens

| Screen | URL | Who |
|---|---|---|
| Approvals: queue with every rule shown next to the button, competing requests, approve / reject with reason | `/approvals/` | `request.approve` |
| Transfers board: to dispatch (how + note), on the way (record a failed attempt, discrepancy or note; resolve), recently received | `/approvals/transfers/` | `transfer.dispatch` |
| Confirm receipt (side panel from My requests): units received, "this replaced a purchase we had planned" | `/approvals/receive/<request>/` | `transfer.receive` for the receiving unit |
| Cancel after approval, before dispatch (from My requests) | `/approvals/cancel/<request>/` (POST) | The requester, or an approver for the owning unit |

## Public interface (`services.py`)

`approval_problem(reviewer, request)`, `approve_request`, `reject_request`, `dispatch`, `record_delivery_event`,
`resolve_event`, `cancel_reservation`, `confirm_receipt`, `queue_for`, `pending_count`, `decided_today`,
`board_for`, `to_dispatch_count`, `transfer_for_request`, `competing`.

## Design decisions

**D1. Approval is one transaction that locks the rows it changes.**
`approve_request` locks the request and the asset (`SELECT … FOR UPDATE`), re-checks every rule, allocates the
units, and creates the decision, reservation and transfer together; any failure saves nothing. *Why:* C5 "the
last item cannot go to two people", NFR-10, NFR-22. A test runs two approvers in two threads at the same moment
for the last unit: one succeeds, the other is refused.

**D2. One function holds every approval rule, and the queue shows it before clicking.**
`approval_problem` checks, in order: still pending; not the approver's own request (BR-5); an item chosen;
approver role for the owning unit; within the role's AED limit; the Institution Blueprint route; still
published (BR-3); enough free units (BR-7). The queue disables Approve and shows the reason ("Above your
approval limit", "Only 0 unit(s) free now"). *Why:* people see why before they try; the same function guards
the real approval, so the screen and the rule cannot disagree.

**D3. Stale screens are caught.**
The Approve button sends the request's row version. If the request changed after the queue was drawn, the
answer is "This changed while you were looking at it" instead of a decision on old data (Table 9.1 `CONFLICT`).
The queue also refreshes itself every minute.

**D4. Competing requests are shown only when they really compete.**
"Competes with N other requests" appears when the requests together want more than is free (BR-13). The
approver decides; the system never picks a winner.

**D5. Rejecting needs a reason and the approver role, but not the value limit.**
An item that ran out, was withdrawn, or is above one's limit can still be turned down with an explanation. The
requester gets the reason by message and e-mail.

**D6. Approval never moves custody.**
Owner, unit, custodian and location change only when the receiver confirms the same quantity that was sent,
after dispatch (BR-8, BR-9, FR-7.16). Part of a lot becomes a new asset record for the receiving unit (design
change B3).

**D7. Problems keep the transfer in transit.**
A failed attempt or a discrepancy is recorded as a delivery event; an open discrepancy blocks receipt until
Facilities resolves it. If the receiver enters fewer units than sent, a discrepancy is recorded instead of a
receipt. Nothing returns to stock by itself (FR-8.16). Delivery events are never edited.

**D8. Cancelling after approval releases the units exactly once.**
Allowed before dispatch, by the requester or an approver for the owning unit. The reservation can be
cancelled only once, so the release cannot run twice (UC-30).

**D9. Verified savings start here.**
The receiver can tick "This replaced a purchase we had planned". It is stored on the transfer
(`replaced_planned_purchase`, new field) and the Sustainability dashboard reports it apart from estimates.
*Why:* the pitch's "verified savings: we confirm a department actually cancelled a purchase".

**D10. Everyone involved hears about each step.**
Approved → requester (in-app and e-mail) and Facilities for the owning unit; rejected → requester with the
reason; dispatched → requester; received → the dispatcher and the previous custodian; discrepancy → the
dispatcher.

## Conflicts with earlier phases

- Requests made from a category without an item cannot be approved until an item is chosen (approvers belong to
  the unit that owns an item). The Matching module (step 7) lets the requester pick one. Phase 3 does not say
  who approves a request with no item; this is the decision taken.
- New field `Transfer.replaced_planned_purchase` (design change 15, added to `docs/design-changes.md`).

## Tests (`tests/test_approvals.py`, `tests/test_transfers.py`)

No self-approval; approvers only; AED limit; the last unit cannot go to two people (sequential and two threads
at once); custody moves only on receipt; part of a lot is split; receipt before dispatch refused; reject needs a
reason, notifies, and cannot be decided twice; cancel after approval releases once; no cancel after dispatch;
only Facilities dispatches; an open discrepancy blocks receipt until resolved; Blueprint rules route to a role;
queue and badge counts; the queue explains blocked requests and competition; a stale approval becomes a
conflict message; the full flow through the screens (approve, dispatch, receive); a short delivery records a
discrepancy.

## Left for later

- Menu badges refresh on the next page load, not instantly after an HTMX action (UI upgrade).
- Arabic translations (step 12).
