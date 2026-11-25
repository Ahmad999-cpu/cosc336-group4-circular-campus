# Module: Users & Access (`apps/access`)

**Delivers:** C1 login and roles · Feature 4.14 (UC-42 to UC-45) · BR-1, BR-2 · NFR-13 to NFR-19
**Brief, Phase 6:** "User registration or administrator-created accounts, authentication and role-based
access control." Lab slide C1: "at least 3 roles: requester, custodian, approver/admin. The server checks
permissions; hiding a button is not enough."
**Owns:** `Department`, `User`, `Permission`, `Role`, `RoleAssignment`, `UserSession`

## Screens

| Screen | URL | Who |
|---|---|---|
| Sign in (with one-click demo accounts while DEBUG is on) | `/accounts/login/` | Everyone |
| People: accounts, units, roles, status, search | `/accounts/people/` | `admin.users` |
| Person side panel: status, roles, details | `/accounts/people/<id>/` | `admin.users` |
| Add person side panel | `/accounts/people/new/` | `admin.users` |
| Change password | `/accounts/password/` | Signed-in users (click your name in the top bar) |

## Public interface

- `permissions.require(user, action, dept, value=)`: raise `Forbidden` unless allowed. Every service calls it first.
- `permissions.can(...)`: the same check, returning True/False.
- `permissions.has_any(user, action)`: "may do this somewhere", only for deciding what to show.
- `decorators.needs(action)`: view guard; returns 403 to people without the permission anywhere.
- `services.create_user`, `update_user`, `set_status`, `assign_role`, `revoke_role`.

## Design decisions

**D1. Permissions are codes, roles are data.**
Services check codes such as `request.approve`, never role names. A role is a named bundle of codes with an
optional AED approval limit. *Why:* C1 needs at least 3 roles, and Institution Blueprint needs each
institution to define its own. Hard-coded roles would mean a rewrite for Blueprint. The demo data has seven
roles based on the Phase 3 actors. *Traces to:* ADR-1, BR-2.

**D2. The check runs on the server, in the service, every time.**
Screens are guarded by `needs()` (403 for people without the permission anywhere) and every service starts
with `require()` for the exact unit. A test calls a service directly, with no screen, and is still refused.
*Why:* lab slide C1; Section 9.8 "every service call re-checks role and departmental scope".

**D3. Scope follows the unit tree.**
A role given for a unit covers that unit and every unit below it; no unit means the whole institution.
*Why:* an approver for the College of Engineering should approve for its departments without one assignment
per department. *Traces to:* `RoleAssignment.covers(dept)`.

**D4. Administrator-created accounts, no self-registration.**
The brief allows either. A university already knows its staff, and self-registration would let anyone
create an account on an internal system. New accounts get a first password the administrator shares
privately; the person changes it after signing in.

**D5. Administration needs an institution-wide role.**
`admin.users` assigned for one unit is not enough to manage accounts. *Why:* account management is a
security function (NFR-14), not a departmental one.

**D6. Nobody can lock out the last administrator.**
Suspending, deactivating or removing the role of the last active institution-wide administrator is refused
with an explanation. *Why:* otherwise one mistake makes the system unmanageable without database access.

**D7. Suspending or deactivating an account ends its sessions at once.**
Their `UserSession` rows are invalidated, so the next request signs them out. History and audit rows stay
(BR-14).

**D8. Every security-relevant event is audited.**
Sign-in, sign-out, failed sign-in (with the e-mail tried, no password), account creation, edits with
before/after values, status changes, role assignments and removals, and every refused permission check.
*Why:* NFR-18.

**D9. Passwords use Argon2id; sessions end after 15 idle minutes.** *Why:* NFR-16 and NFR-17.

**D10. Demo sign-in exists only while DEBUG is on.**
The sign-in page offers one-click buttons for the six demo accounts from `seed_demo`. The endpoint returns
404 when DEBUG is off, and only accepts those six addresses. *Why:* the lab demo needs fast role switching
without exposing anything in production.

**D11. Business errors become messages, not crashes.**
`apps/web/middleware.py` turns `Forbidden` into the 403 page and any other `DomainError` into a toast,
leaving the person on the page they were on. *Why:* "errors say what went wrong and how to fix it".

## Conflicts with earlier phases

- None found. Phase 3 lists "Lecturer or Departmental Administrator: use only the roles and asset scopes
  explicitly assigned; no automatic inheritance of custodian privileges". Scope inheritance (D3) applies only
  down the unit tree, never across roles, so this still holds.

## Tests (`tests/test_access.py`)

Sign-in works and is audited; a wrong password is refused and audited; a deactivated account cannot sign in;
demo sign-in is off in production; passwords are Argon2; the People screen is for administrators only; the
service refuses non-administrators even without a screen; a unit-scoped administrator is not enough; create,
assign and revoke with audit; duplicate e-mails are refused; the last administrator cannot be locked out;
suspending ends the person's sessions; the side panel's role change works over HTMX with a toast.

## Left for later

- Arabic translations of these screens (step 12).
- Units are edited in the Django admin for now; the Blueprint screen (step 11) will edit them in the app.
