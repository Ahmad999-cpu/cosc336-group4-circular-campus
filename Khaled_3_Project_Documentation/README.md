# Circular Campus — design documentation for the implementation

The Phase 4 & 5 design document is the source of the design. These files record what the code does with it:
one file per module explaining its design decisions, and one file listing every change from the design.

- [design-changes.md](design-changes.md) — every place the code adds to or differs from Phase 4 & 5
- `modules/` — one document per module (below)

## Modules, owners and what each one delivers

Owners: fill in your names. One owner per module; a person can own several.

| Module | Doc | Owner | Lab requirement it delivers |
|---|---|---|---|
| Users, Access | [access.md](modules/access.md) | _TBD_ | C1 login and roles |
| Institution Blueprint | [blueprint.md](modules/blueprint.md) | _TBD_ | Bonus: Institution Blueprint |
| Assets & Catalogue | [catalogue.md](modules/catalogue.md) | _TBD_ | C2 assets, C3 publish and search |
| Requests & Reservations | [resource_requests.md](modules/resource_requests.md) | _TBD_ | C4 request and track |
| Approvals & Transfers | [transfers.md](modules/transfers.md) | _TBD_ | C5 approve and transfer |
| Life Cycle & Maintenance | [lifecycle.md](modules/lifecycle.md) | _TBD_ | C6 states and history |
| Matching | [matching.md](modules/matching.md) | _TBD_ | AI 2 matching and ranking (required) |
| Reporting | [reporting.md](modules/reporting.md) | _TBD_ | C9 basic report, AI 5 generated report (required) |
| Sustainability | [sustainability.md](modules/sustainability.md) | _TBD_ | C7 dashboard; bonus: savings calculator, net-cost comparison |
| Notifications | [notifications.md](modules/notifications.md) | _TBD_ | C8 notifications |
| Audit | [audit.md](modules/audit.md) | _TBD_ | NFR-18 audit log |
| AI Gateway | [ai.md](modules/ai.md) | _TBD_ | Shared by AI 1–5; AI 1 classification and photo capture |
| Web shell | [web.md](modules/web.md) | _TBD_ | Layout, navigation, Arabic/English switch, worker, demo data |

## Plan

**Phase 6 draft (labs, week of 22 Nov):** C1–C6, AI 2 (matching) and AI 5 (generated report), with a basic
version of C9 so AI 5 has numbers to summarise.

**By 6 Dec:** C7–C9 in full, AI 1 (classification / photo capture), savings calculator, net-cost comparison,
Institution Blueprint setup screen and AI drafting, Arabic translations.

## What the skeleton already contains

- All 34 classes of Figure 5.1 as Django models, with their operations and the 7 state machines.
- Server-side permission checks, data-driven roles, approval limits and Blueprint approval routing.
- The approval transaction and receipt confirmation (the hardest rules of C5), with tests, including two
  approvers approving the last unit at the same moment.
- AI Gateway with time limits, redaction, model versions, inference log and an offline fake provider.
- Savings calculator with the agreed formula.
- Login, home page, Arabic/English switch with right-to-left layout, worker, demo data.

Everything marked `TODO(<module> owner)` or `raise NotImplementedError` is for the module owner.
