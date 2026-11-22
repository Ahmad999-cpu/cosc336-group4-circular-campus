# Module: Life Cycle & Maintenance (`apps/lifecycle`)

**Delivers:** C6 states and history · maintenance and repair tracking (Phase 6 minimum) · Features 4.9 and 4.10
(UC-10 to UC-16, UC-49) · BR-10, BR-11, BR-14 · NFR-27
**Lab slide C6:** "Allow only the moves in the cycle above. Show for each asset who did what, and when."
**Brief:** "asset life cycle history that records acquisition, allocation, utilization, inspection, maintenance,
repair, transfer, refurbishment, donation, recycling, retirement, and disposal events"; "maintenance and repair
module through which authorized users can report defects, request inspection, record repair actions, monitor
status, capture costs, and update the asset's condition after service".
**Owns:** `LifeCycleEvent`, `EndOfLifeProposal`, `MaintenanceRecord`, `InspectionRequest`, `RepairAction`,
`MaintenanceUpdate`

## Screens

| Screen | URL | Who |
|---|---|---|
| Asset history: every event with who and when, state now, **allowed next moves**, corrections | `/lifecycle/asset/<id>/` | Anyone who can see the asset |
| Report a problem (defect or inspection), side panel from the asset | `/lifecycle/asset/<id>/report/` | `maintenance.record` for the unit |
| Propose end of life (retire, donate, recycle, dispose), side panel | `/lifecycle/asset/<id>/end-of-life/` | `eol.propose` for the unit |
| Maintenance board: open records by severity (start work, record repair with cost, back in service), recently closed; End of life tab (approve / reject with reason, record it's done) | `/lifecycle/` | `maintenance.record` or `eol.approve` |

## Public interface (`services.py`)

`history`, `next_states`, `correct_event`, `report_problem`, `start_work`, `record_repair`, `return_to_service`,
`maintenance_for`, `open_maintenance_count`, `propose_end_of_life`, `decide_end_of_life`, `complete_end_of_life`,
`proposals_for`, `attention_count`.

## Design decisions

**D1. History is written automatically and never edited.**
Every Asset operation sends a signal; this module writes the event in the same transaction, so history can't be
skipped (BR-10). Maintenance, repair and end-of-life steps add their own events. Rows refuse updates and
deletes; a mistake gets a correction row that points at the wrong one (NFR-27, BR-14).

**D2. C6 made visible: the history page shows the allowed next moves.**
"Allowed next" lists the states the Figure 7.5 machine permits from the current state (for example Available →
Reserved, Under maintenance, Retired), or "None: this is a final state". *Why:* the lab demo can show that only
the moves in the cycle are possible, not just say so.

**D3. Reporting a problem doesn't take the item out of service; starting work does.**
A defect or inspection is recorded at once (one open record per asset). When maintenance staff start work, the
asset moves to Under maintenance and leaves the marketplace, which is refused while units are reserved ("no
commitments" guard, Figure 7.5).

**D4. A repair alone never makes an item available again.**
A successful repair moves the record to Repair completed; only the custodian's "Back in service", with the
condition after repair, closes the record and makes the asset Available (FR-10.18). An unsuccessful repair moves
to Further repair required and can start again (Figure 7.9).

**D5. Repair costs are captured.** Each repair stores what was done, the result and the cost in AED, shown on
the board and in the history. The Sustainability module uses these costs in the net-cost comparison.

**D6. End of life needs a second person.**
A custodian proposes (no reserved units allowed); someone else with `eol.approve` approves or rejects with a
reason (the proposer is refused, FR-9.22); then the custodian records that it happened, which moves the asset to
Retired and then Donated, Recycled or Disposed with the approval as reference (BR-11). Dispose carries the note
"only when it can't be reused, donated or recycled".

**D7. Severity orders the board.** Critical, then High, Medium, Low; oldest first within each.

## Added to other modules

- `apps/catalogue/views.py` and `_panel_body.html`: "Report a problem", "Propose end of life" and "Full history"
  in the asset side panel, shown by permission.
- `apps/web/navigation.py`: Maintenance badge counts open records and proposals to review.

## Conflicts with earlier phases

- Phase 3 lists "Maintenance Staff" with inspect/record permissions; Phase 4–5 also lets custodians record
  maintenance. The demo roles give `maintenance.record` to both; Blueprint can change that per institution.

## Tests (`tests/test_lifecycle.py`)

The full repair cycle (report → start → repair → still under maintenance → only the custodian returns it →
Available) with history events; unsuccessful repair loops; no maintenance while reserved; requesters cannot
report; end of life needs an independent reviewer and ends Donated via Retired; rejection needs a reason and
blocks completion; no end of life with commitments; corrections are new rows; the history page shows allowed
moves and names; the board flow over HTMX; requesters have no board.
