# Module: Requests & Reservations (`apps/resource_requests`)

**Delivers:** C4 request and track · Features 4.5 and 4.6 (UC-23 to UC-25, UC-50; reservations UC-29 to UC-31
are created and cancelled by Approvals & Transfers) · BR-4, BR-6
**Brief:** "departmental resource-request module that allows users to specify the required resource category,
purpose, specifications, quantity, preferred condition, urgency, location, and required date"; "express
interest in an available asset and track the status of the request". Lab slide C4: "Let staff submit a request
and see the status of their own requests."
**Owns:** `ResourceRequest`, `Reservation`, `ReservationEvent`, `AssistantDraft`

## Screens

| Screen | URL | Who |
|---|---|---|
| New request: full page from an item (`?asset=`), or a side panel from Find; or from scratch with a category | `/requests/new/` | `request.submit` |
| My requests: Open / Closed / All, progress steps for each | `/requests/` | `request.submit` |
| Request side panel: details and "What happened" timeline | `/requests/<id>/` | The person who made it |
| Edit (side panel) and Cancel (inline, reason required) while pending | `/requests/<id>/edit/`, `/requests/<id>/cancel/` | The person who made it |

## Public interface (`services.py`)

`submit_request(by, data, idempotency_key) -> (request, created)`, `edit_request`, `cancel_request`,
`my_requests(user, which)`, `request_units(user)`, `attention_count(user)` (menu badge),
`progress_index(request)` (0 sent, 1 approved, 2 on its way, 3 received).

## Design decisions

**D1. A request names the item when it can.**
Most requests start from an item in Browse or Find, so the asset is selected up front and its category is
taken from it. A request can also start from a category alone (the brief's "required resource category"); the
Matching module then suggests items. *Why:* fewer steps for the common case, still meets UC-23.

**D2. One form, one click, one request.**
Every form carries a random idempotency key. Sending it twice (double click, slow network, back button)
returns the first request. A race on the same key is caught by the database's unique constraint. *Why:*
Table 9.1 `DUPLICATE (returns original)`.

**D3. Rules are checked on submit, not only in the browser.**
At least one unit; no more than the free units; a needed-by date from today on; a purpose; the requester's
role covers the unit they ask for; not an item their unit already owns; the item still published. The
quantity stepper also stops at the free units, but the server decides. *Why:* BR-4, C1.

**D4. Asking does not reserve.**
Submitting never touches quantities; the units are reserved only when an approver approves (BR-6). The form
says so: "Nothing moves until they approve and you confirm receipt."

**D5. The approvers hear about it.**
Everyone whose role may approve for the item's owning unit gets an in-app message; the requester gets an
in-app message and an e-mail (outbox, ADR-4). *Why:* C8.

**D6. Only the requester changes their request, and only while pending.**
Edit and Cancel need the same person and a pending request with no reservation (UC-25). Cancelling needs a
reason. After approval, cancelling goes through Approvals & Transfers, which releases the reserved units
exactly once (UC-30). *Why:* BR-14; a closed request can never be decided again.

**D7. Progress in four steps people understand.**
Sent → Approved → On its way → Received, drawn the same on every card; Rejected and Cancelled show the reason
instead. *Why:* C4 "see the status of their own requests" at a glance.

**D8. "Buying these new would cost about…"**
When an item is selected, the form shows the register value × quantity and updates as the quantity changes.
The full net-cost comparison (transport, storage, repair) comes with the Sustainability module (bonus feature,
step 10). *Why:* shows the point of reuse at the moment of asking.

## Added to other modules

- `apps/access/permissions.py`: `users_who_can(action, dept)` (who to notify).
- `apps/access/views.py`: four more demo accounts on the sign-in page (club president, second custodian,
  university-wide approver, technician).
- `static/css/theme.css`: the quantity stepper keeps its own width.

## Conflicts with earlier phases

- Phase 3 shows the requester's "Department Representative" as the actor for requests. The code lets anyone
  with `request.submit` for a unit request for it, so a department can give that permission to its
  representative only. No change to the design needed.

## Tests (`tests/test_requests.py`)

Submit creates a pending request and notifies the requester and approvers; the same key returns the first
request; more than the free units, a unit outside the person's scope, a past date and a missing category are
refused; a request without an item works; only the owner edits and cancels, cancelling needs a reason, a
cancelled request cannot be edited; progress index; the new-request page from an item, double submit makes one
request, My requests lists it; too many units shows a field error; other people get 404 on someone's request;
cancel over HTMX redirects back with a toast.

## Left for later

- Confirm receipt and cancel-after-approval buttons appear on the cards once step 5 is in.
- Find (step 7) opens this form in a side panel with the description already filled in.
