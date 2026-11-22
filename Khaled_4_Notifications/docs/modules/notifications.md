# Module: Notifications (`apps/notifications`) — C8

**Delivers:** C8 ("messages when a request is made, approved, rejected or received") · ADR-4 outbox ·
FR-2.13, FR-3.17, FR-5.20 (a mail failure never rolls back the business action)
**Owns:** `Notification`

## Screens

| Screen | URL | Who |
|---|---|---|
| Bell in the top bar: unread count, the 6 latest (each opens what it is about), "Mark all as read" | every page | signed in |
| Notifications page: All / Unread, grouped Today · Yesterday · Earlier, an icon per kind, "Mark all as read" | `/notifications/` | signed in |
| Open one: marks it read and goes to the right screen | `/notifications/<id>/` | the recipient only |

## Public interface (`services.py`)

`enqueue(recipient, event_type, message, subject_ref, email=False)` (called by other modules inside their own
transaction), `inbox`, `unread_count`, `mark_read`, `mark_all_read`, `grouped`, `target_url`.

## Who is told what (C8 coverage)

| Event | Recipients | Where the link goes |
|---|---|---|
| Request made | requester (confirmation), approvers of the owning unit (e-mail too) | My requests / Approvals |
| Item chosen for a request (Step 7) | approvers of the owning unit | Approvals |
| Approved | requester (e-mail too), facilities | My requests / Transfers |
| Rejected (with reason) | requester (e-mail too) | My requests |
| Dispatched | requester (e-mail too) | My requests |
| Received | facilities who dispatched it, source custodian | Transfers / Our assets |
| Delivery problem, cancellation, maintenance, end of life | the people involved | the matching board |

## Design decisions

**D1. Outbox (ADR-4).** In-app rows are visible at once; e-mail rows wait as Pending for `runworker`, which
marks them Sent or Failed with the reason. *Why:* an approval must never fail because the mail server is down.

**D2. Links are worked out when a notification is opened, not stored.** The `subject_ref`
(`ResourceRequest:<id>`, `Transfer:<id>`…) plus who is reading decides the screen: the requester goes to their
request card, an approver to the queue, facilities to the board, a custodian to Our assets. *Why:* the same
event means different work for different people, and URLs can change without breaking old notifications.

**D3. Only the recipient can open or mark a notification** (403 otherwise), and "Mark all as read" only
redirects back inside the site (no open redirect).

**D4. Badges stay live (fixes the known issue from Step 1).** Every action that shows a toast also fires
`cc:refresh`; the page then asks `/badges/` for the menu counts and unread number and updates them with a small
bump. They also refresh every minute while the tab is visible. *Why:* an approver working through the queue
saw "Approvals 5" until they reloaded.

**D5. Notifications are short, plain sentences** naming the item and quantity ("Not approved: 2 × Dell monitor.
Reason: …"), so the bell is useful without opening anything.

## Added to other modules

- `templates/base.html`: bell items are links, "Mark all as read", `data-nav` on menu links, counts always
  rendered (hidden when 0) so they can be updated.
- `apps/web/views.py` + `urls.py`: `badges` JSON endpoint. `apps/web/htmx.py`: `with_toast` adds `cc:refresh`.
- `static/js/app.js`: `CC.refreshBadges`. `theme.css`: inbox list, bump animation.

## Known limitation (for Step 12)

Messages are written in English when the event happens. The Arabic interface translates every label around
them; translating the stored sentences needs each person's language at the time of sending and is planned with
the Arabic step.

## Tests (`tests/test_notifications.py`, 9 tests)

Made → approved → dispatched → received each notify the right people; rejection carries the reason; with a
broken mail server the approval still commits and the worker marks every e-mail Failed with a reason; links
follow the reader (requester vs approver vs unknown); opening marks read and redirects; someone else's
notification is 403; page tabs, "Mark all as read" and no open redirect; `/badges/` counts; actions trigger
`cc:refresh`.
