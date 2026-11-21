# Module: Institution Blueprint (`apps/blueprint`) — bonus feature

**Delivers:** the bonus "Institution Blueprint": an administrator describes the institution once (its units,
member types and who approves what) and every screen reads its rules from that description. Includes an
AI-assisted setup that a person reviews before anything changes.
**Owns:** `ApprovalRule`, `BlueprintDraft` (units and member types live in `access` as `Department` and `Role`;
design changes 4–6)

## Screens (all need `admin.blueprint`; menu item "Setup")

| Tab / screen | URL | What it does |
|---|---|---|
| **Units** | `/setup/?tab=units` | The unit tree (drawn with connectors), each unit's own word for its kind, campus, people and items; add a unit anywhere (＋ on a row adds one inside it), edit, move, deactivate/reactivate |
| **Member types** | `/setup/?tab=roles` | A permission matrix: every member type × the 16 permissions grouped (Assets, Requests, Transfers, Care, Impact, Admin), people count and approval limit; edit in a side panel with tick-boxes |
| **Approval routes** | `/setup/?tab=routes` | Routes in priority order with on/off switches; add/edit in a side panel ("When a request is for… it must be approved by…"); **Who would approve?** tester: pick an item and quantity, see the route that applies and the people who could approve it today |
| **Quick start** | `/setup/?tab=start` | Start from a University / School / Hospital template, or **describe the institution in your words** and let the AI draft a setup |
| **Review the draft** | `/setup/drafts/<id>/` | Every unit, member type and route the draft would add, each with a tick-box, "already exists" or a problem to fix; Publish ticked items or Discard |

## Public interface (`services.py`, `routing.py`)

`unit_tree`, `save_unit`, `set_unit_status`, `save_role`, `role_matrix`, `save_rule`, `toggle_rule`,
`describe_rule`, `who_approves`, `draft_from_template`, `draft_from_description`, `normalise_draft`, `review`,
`publish_draft`, `discard_draft`; `routing.approval_route(asset, quantity)` (used by Approvals since Step 5).

## Design decisions

**D1. The Blueprint is the data the rest of the system already reads.** Units are `Department` rows with a
parent; member types are `Role` rows with permission codes and an AED limit; routes are `ApprovalRule` rows
read inside every approval transaction. Change a limit here and the next approval uses it — there is no
second rules engine to disagree with.

**D2. First matching route wins, by priority.** A route can match a category subtree and a total value range;
the approver comes from the owning unit, its parent unit, or anywhere in the institution. With no matching
route, anyone who can approve for the owning unit may, within their limit — so a fresh install works.

**D3. Safety rails.** A unit can't be moved inside itself; a unit with active sub-units or with assets can't be
deactivated; the last member type that holds "Edit the Institution Blueprint" (with people in it) can't lose it;
a route's approver must actually have "Approve or reject requests"; From can't exceed Up to. Every change is
written to the audit log with before/after.

**D4. The tester explains the routing.** "Who would approve?" shows the route, the role and unit, and the
people who could approve today, already filtered by their AED limits; if nobody can, it says so. *Why:* routing
rules are easy to get wrong and hard to see; this makes them testable in the demo.

**D5. The AI drafts, a person publishes (Section 9.8, BR-12).** The description goes through the AI Gateway
(`draft_blueprint`, prompt in `ai/providers/anthropic.py`, permission codes passed in so it can only use real
ones). The reply is normalised (unknown fields dropped, types fixed), stored as a `BlueprintDraft`, and
reviewed item by item. Publishing writes the ticked items in one transaction; any problem in a ticked item
stops everything and nothing is written.

**D6. Publishing is additive.** Units and member types that already exist (same name) are kept exactly as they
are; only new ones are created, parents first whatever order the draft lists them in. *Why:* re-running a
template must never overwrite limits an institution already tuned.

**D7. Works offline.** The three templates need no AI. Without an API key the fake provider picks the closest
template from keywords (hospital / school / university), so the review flow can be demonstrated.

**D8. Your own words.** Units keep the institution's own word for their kind (College, Ward, Grade, Lab), and
member types have an Arabic name field, so a school or hospital doesn't have to pretend to be a university.

## Added to other modules

- `apps/ai/providers/anthropic.py`: `draft_blueprint` with its prompt; `fake.py`: offline template draft.
- `seed_demo`: an active BLUEPRINT model version. `apps/web/navigation.py`: "Setup" menu item.
- `config/urls.py`: prefix `/setup/`. `theme.css`: tree, permission matrix, routes, templates, draft review.

## Conflicts with earlier phases

- **Multi-step approvals** ("Head of Department, then Finance") stay future work: the ERD allows one
  `ApprovalDecision` per request (design change B4, unchanged).
- **Visibility rings and priority rules** (Phase 5 Blueprint ideas) are not built; the module doc for Phase 7
  lists them as future work.

## Tests (`tests/test_blueprint.py`, 15 tests)

Units: create/edit/tree depth, audit, no loops, no deactivation with sub-units or assets, admins only. Member
types: permissions and limit with "10,000" input, duplicate names, unknown permissions, can't lock everyone out
of the Blueprint. Routes: priority + category + value with parent-unit scope and fall-through, approver must be
able to approve, From ≤ Up to, on/off switch, the tester (route, people, limit filtering). Drafts: template →
review → publish additively (existing units kept, parents first), problems block publishing with nothing
written, unticked items skipped, a route needs its member type, AI draft normalised, AI timeout falls back to a
message. Screens: all four tabs, unit drawer and save, tester, template → draft page → publish, 403 for
non-admins.
