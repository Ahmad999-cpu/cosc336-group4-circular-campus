Section 4 

4.4 Asset Search and Filtering
4.4.1 Description and Priority
Authorized Department Representatives and Asset Custodians can search published assets, combine filters, and inspect current asset details. Results are restricted by user permissions and current publication and availability information. Searching or viewing does not reserve an asset.
Priority: High (Must Have)
4.4.2 Stimulus Response Sequences
Search Available Assets
The user opens Available Assets, enters a name, keyword, or description, and submits the search. The system searches accessible published assets and returns matching results. An empty search lists all accessible published assets; no matches produces a clear message.
Filter Available Assets
The user chooses one or more category, condition, department, location, quantity, availability, age, estimated value, or life-cycle-state filters and selects Apply Filters. The system validates values and displays assets satisfying all selected filters and any search text. Clear Filters removes filters while retaining the search text.
View Asset Search Result Details
The user selects a result. The system rechecks permission, publication, and availability and displays the current asset details. For example, a department can search for monitors, filter for two available units, and inspect their condition before submitting a request.
4.4.3 Functional Requirements
FR-4.1: The system shall allow authenticated Department Representatives and Asset Custodians to search published assets they are authorized to view.
FR-4.2: The system shall accept an asset name, keyword, or description as search input.
FR-4.3: The system shall return accessible published assets whose name or description contains the entered search text, using case-insensitive text matching.
FR-4.4: The system shall display all accessible published assets when no search text or filters are provided.
FR-4.5: The system shall allow filtering by category, condition, department, location, available quantity, availability, asset age, estimated value, and current life-cycle state.
FR-4.6: The system shall apply all selected filters together and combine them with the current search text.
FR-4.7: The system shall validate numeric filters and reject negative quantities, ages, or values and ranges whose minimum exceeds their maximum.
FR-4.8: The system shall allow the user to change filters or clear them without modifying asset records.
FR-4.9: The system shall display each result with its asset identifier, name, category, department, location, condition, available quantity, availability, and life-cycle state.
FR-4.10: The system shall display a clear message when no assets satisfy the search or filter criteria.
FR-4.11: The system shall allow users to select a result and view its current description, specifications where recorded, purchase date, age, estimated value, and available supporting information in addition to the result fields.
FR-4.12: The system shall recheck access permission, publication status, and current availability before displaying a selected asset as available.
FR-4.13: The system shall inform the user if a result is no longer published or available and allow a return to refreshed results.
FR-4.14: The system shall prevent searches, filters, and detail views from reserving quantities, approving requests, or modifying asset data.
FR-4.15: The system shall deny access to restricted listings and details without revealing their protected content.
FR-4.16: The system shall display a retrieval error and allow retry without changing the current search criteria when search or detail retrieval fails.
FR-4.17: The system shall identify missing age or estimated-value information as unavailable and exclude such an asset from a filter that requires that missing value.
4.5 Resource Requests
4.5.1 Description and Priority
Authorized Department Representatives can submit, view, and update departmental resource requests. Requests record the operational need and remain Pending Approval until an authorized reviewer decides. An asset may be selected from available listings or suitable recommendations; submitting a request does not reserve it.
Priority: High (Must Have)
4.5.2 Stimulus Response Sequences
Submit Resource Request
The Department Representative opens the request form and enters the category, purpose, specifications, quantity, preferred condition, urgency, destination, and required date. A selected asset may be linked. The system validates the request, saves it as Pending Approval for the represented department, and displays and emails confirmation.
View Resource Request
The representative opens Resource Requests and selects an accessible record. The system displays its details, status, decision reason if applicable, and linked reservation or transfer references without changing the record.
Update Resource Request
The representative selects Edit Request on an eligible Pending Approval request and submits changes. The system validates authority, status, and current data and saves the changes with a timestamp. For example, a department can change its requested monitor quantity from two to three before approval.
Cancel Pending Resource Request
The representative selects Cancel Request on a Pending Approval request, enters a reason and confirms. The system rechecks authority and status and saves Cancelled with an audit record. If approval occurred in the meantime, the system directs the user to the reservation workflow instead.
4.5.3 Functional Requirements
FR-5.1: The system shall allow authorized Department Representatives to submit requests only for departments they are permitted to represent.
FR-5.2: The system shall capture resource category, purpose, specifications, positive whole-number quantity, preferred condition, urgency, destination location, and required date.
FR-5.3: The system shall require category, purpose, specifications, quantity, urgency, destination, and required date before submission and allow preferred condition to be recorded as Any.
FR-5.4: The system shall reject missing mandatory values, nonpositive or fractional quantities, and a required date earlier than the submission date.
FR-5.5: The system shall allow a representative to link an accessible published asset selected through search or AI matching to a resource request without reserving it.
FR-5.6: The system shall validate a selected asset reference and record its identifier separately from the requested resource specifications.
FR-5.7: The system shall assign a unique request identifier and record the requesting user, represented department, and submission timestamp.
FR-5.8: The system shall save a valid new request with status Pending Approval and make an asset-linked request available to the responsible authorized reviewer.
FR-5.9: The system shall retain an unlinked resource request as Pending Approval until a suitable asset has been selected; approval shall require a valid asset link.
FR-5.10: The system shall allow representatives to view their accessible requests and their current details, status, decision reasons where applicable, and linked reservation and transfer references.
FR-5.11: The system shall display an appropriate message when no accessible requests exist or a selected request cannot be found.
FR-5.12: The system shall allow authorized representatives to update request details or the selected asset only while the request is Pending Approval and has no active reservation or transfer.
FR-5.13: The system shall recheck request status, authority, and submitted field values immediately before saving an update.
FR-5.14: The system shall reject updates to Approved, Rejected, Fulfilled, or Cancelled requests without changing their saved details.
FR-5.15: The system shall record the updating user and timestamp and preserve the earlier request details in the audit history.
FR-5.16: The system shall display a confirmation pop-up and send confirmation email to the representative after successful submission or update.
FR-5.17: The system shall allow cancellation of an unsubmitted form without creating a request or saving edits.
FR-5.18: The system shall deny unauthorized viewing, submission, or modification of another department's requests.
FR-5.19: The system shall preserve the previous record if saving fails and prevent duplicate requests from a repeated submission of the same operation.
FR-5.20: The system shall inform the representative if confirmation email delivery fails while retaining the successfully saved request and its on-screen confirmation.
FR-5.21: The system shall allow an authorized Department Representative to cancel their department's Pending Approval request after providing a reason and confirmation.
FR-5.22: The system shall recheck that a request is Pending Approval and has no active reservation or transfer before saving its cancellation, reason, actor and timestamp.
FR-5.23: The system shall preserve the previous request if cancellation fails and prevent repeated cancellation from changing asset quantities; Approved requests shall use the reservation cancellation workflow.
4.6 Reservation Management
4.6.1 Description and Priority
Reservations allocate asset quantities only after approval. Authorized Department Representatives and Asset Custodians can view reservations, cancel eligible reservations before dispatch, and review history. Creation is part of the approval workflow in use case UC-33; it is not a separate action available before approval.
Priority: High (Must Have)
4.6.2 Stimulus Response Sequences
Create Reservation After Approval
When the authorized custodian confirms an eligible approval, the system rechecks available quantity and creates one linked Active reservation as part of the same saved operation. For example, reserving two of five available monitors leaves three available for other requests.
View Reservation
The user opens Reservations and selects an accessible reservation. The system displays the linked request, asset, quantity, requesting department, creation time, and current status.
Cancel Reservation
The user selects Cancel Reservation, supplies a reason, and confirms. The system checks permission, Active status, and that dispatch has not occurred, then cancels the reservation and associated request and releases the quantity once.
View Reservation History
The user opens a reservation and selects View History. The system displays creation, cancellation, and fulfilment events in chronological order, including responsible users, timestamps, and reasons.
4.6.3 Functional Requirements
FR-6.1: The system shall create a reservation only when an authorized asset request is approved through the approval workflow.
FR-6.2: The system shall create the request approval, linked reservation, and quantity allocation as one operation and preserve all previous records if any part fails.
FR-6.3: The system shall recheck the approved quantity against current unreserved available quantity before allocating it.
FR-6.4: The system shall reject a nonpositive or noninteger reservation quantity and prevent allocations exceeding available quantity, including simultaneous approvals.
FR-6.5: The system shall assign a unique reservation identifier and store the linked request, asset, quantity, requesting department, creating user, and creation timestamp.
FR-6.6: The system shall set a newly created reservation to Active and prevent duplicate reservations for the same approved request.
FR-6.7: The system shall allow authorized Department Representatives and Asset Custodians to view reservations within their permissions.
FR-6.8: The system shall display reservation identifier, linked request, asset, quantity, department, creation timestamp, and current status.
FR-6.9: The system shall display a clear message when no accessible reservations exist or a selected reservation cannot be found.
FR-6.10: The system shall allow an authorized user to cancel an Active reservation before the associated asset has been dispatched.
FR-6.11: The system shall require a cancellation reason and explicit confirmation before cancelling a reservation.
FR-6.12: The system shall recheck authorization, reservation status, and dispatch status before committing a cancellation.
FR-6.13: The system shall save the Cancelled reservation, Cancelled request, released quantity, reason, actor, and timestamp as one operation.
FR-6.14: The system shall prevent cancellation after dispatch and direct the user to authorized resolution of the transfer.
FR-6.15: The system shall prevent repeated cancellation from releasing the same quantity more than once and prevent cancellation of a Fulfilled reservation.
FR-6.16: The system shall mark a reservation Fulfilled only when the associated transfer receipt is successfully confirmed.
FR-6.17: The system shall allow authorized users to view chronological reservation creation, cancellation, and fulfilment history with user, timestamp, and reason where applicable.
FR-6.18: The system shall preserve reservation history after cancellation or fulfilment and display the creation event when no later events exist.
FR-6.19: The system shall allow a user to abandon cancellation before confirmation without changing quantities or records.
FR-6.20: The system shall deny unauthorized access or cancellation and display retrieval or save errors without partial changes.
4.7 Approval Management
4.7.1 Description and Priority
Authorized Asset Custodians review pending requests for assets under their responsibility, approve eligible quantities, or reject requests with a reason. A custodian acting as reviewer cannot decide their own request. Approval reserves quantities but does not dispatch the asset or change destination custody.
Priority: High (Must Have)
4.7.2 Stimulus Response Sequences
View Pending Requests
The Asset Custodian opens Approval Management. The system displays eligible Pending Approval requests for assets under that custodian's responsibility. Selecting a request displays its purpose, quantity, destination, required date, and current asset availability.
Approve Asset Request
The custodian selects Approve and confirms. The system rechecks reviewer authority, separation from the requester, pending status, selected asset, and available quantity. It saves approval, reservation, and quantity allocation together and records the decision. For example, a request for three monitors cannot be approved when only two remain available.
Reject Asset Request
The custodian selects Reject, enters a reason, and confirms. The system validates authority, reviewer independence, pending status, and the reason, then saves Rejected with the reviewer and timestamp. It creates no reservation and changes no available quantity.
4.7.3 Functional Requirements
FR-7.1: The system shall allow an authorized Asset Custodian to view Pending Approval requests linked to assets under their responsibility.
FR-7.2: The system shall display requester, department, selected asset, purpose, quantity, destination, required date, and current availability for each selected request.
FR-7.3: The system shall display a message when no pending requests require review and refresh the displayed status if a request has already been processed.
FR-7.4: The system shall allow the responsible authorized Asset Custodian to approve or reject a Pending Approval request after explicit confirmation.
FR-7.5: The system shall prevent a requester from approving or rejecting their own request.
FR-7.6: The system shall recheck reviewer authority and the request's pending status immediately before saving any decision.
FR-7.7: The system shall require an accessible selected asset and a positive whole-number requested quantity before approval.
FR-7.8: The system shall recheck publication, eligible asset state, and current available quantity before approval and reject an allocation exceeding availability.
FR-7.9: The system shall leave the request Pending Approval and explain the shortage or asset ineligibility when approval cannot proceed.
FR-7.10: The system shall save Approved status, a single linked Active reservation, and the corresponding quantity allocation as one operation.
FR-7.11: The system shall prevent simultaneous or repeated decisions from approving the same request twice or allocating the same available quantity more than once.
FR-7.12: The system shall record the reviewer, decision, and timestamp for every completed approval or rejection.
FR-7.13: The system shall require a nonblank reason before saving a rejection.
FR-7.14: The system shall save a rejected request as Rejected without creating a reservation or changing asset quantities.
FR-7.15: The system shall make the recorded status and rejection reason where applicable available to the authorized requester and display confirmation to the reviewer.
FR-7.16: The system shall prevent request approval from changing destination custody or location or recording asset dispatch.
FR-7.17: The system shall allow a reviewer to cancel confirmation without changing the request or quantities.
FR-7.18: The system shall deny a decision outside the reviewer's authority and preserve request, reservation, and quantity records if saving the decision fails.
4.8 Transfer Management
4.8.1 Description and Priority
Authorized Facilities Department Personnel dispatch approved reserved assets, and Receiving Department Representatives confirm delivery. Transfers record source, destination, arrangements, dispatch, receipt, delivery exceptions, and custody changes. Custody and destination location change only after valid receipt confirmation.
Priority: High (Must Have)
4.8.2 Stimulus Response Sequences
Record Asset Dispatch
Facilities personnel select an approved request with an Active reservation, enter or review collection or delivery arrangements, source, destination, and quantity, and confirm dispatch. The system validates the operation and saves In Transit with the responsible user and timestamp.
View Transfer Status
An authorized user selects a transfer. The system displays status, source, destination, quantities, arrangements, dispatch and receipt timestamps, and recorded delivery attempts or discrepancies.
Confirm Asset Receipt
The receiving representative checks the delivery, enters received quantity, and confirms. If it matches dispatch, the system saves receipt, Completed transfer, Fulfilled reservation and request, and custody and location changes together. For example, confirming receipt of two monitors completes their move to the requesting department.
Record Delivery Attempt
Facilities personnel record an unsuccessful delivery attempt or a corrected delivery arrangement against an In Transit transfer. The system saves the reason, timestamp, and responsible user without completing the transfer or releasing the reservation.
4.8.3 Functional Requirements
FR-8.1: The system shall make an approved request with an Active reservation available for creation of one linked transfer record in Awaiting Dispatch state.
FR-8.2: The system shall assign a unique transfer identifier and record the request, reservation, asset, source department and location, destination department and location, quantity, and collection or delivery arrangements.
FR-8.3: The system shall allow authorized Facilities Department Personnel to enter and confirm dispatch details for transfers awaiting dispatch.
FR-8.4: The system shall recheck approval, Active reservation, dispatch authority, source and destination, and a positive whole-number quantity equal to the reserved quantity before dispatch.
FR-8.5: The system shall prevent dispatch of a cancelled or fulfilled reservation and prevent duplicate dispatch of a transfer already In Transit or Completed.
FR-8.6: The system shall save dispatch details, responsible personnel, timestamp, and In Transit status as one operation.
FR-8.7: The system shall retain the Active reservation and existing custody and location until receipt is confirmed.
FR-8.8: The system shall allow authorized Facilities Department Personnel and Receiving Department Representatives to view permitted transfers and their current details and status.
FR-8.9: The system shall display dispatch and receipt timestamps, arrangements, recorded delivery attempts, and unresolved discrepancies when available.
FR-8.10: The system shall allow only a representative authorized for the destination department to confirm receipt of an In Transit transfer with an Active reservation.
FR-8.11: The system shall require the received quantity to match the dispatched quantity before completing a transfer.
FR-8.12: The system shall record a quantity discrepancy with the reporting user and timestamp and block completion until authorized Facilities personnel and the receiving representative resolve it.
FR-8.13: The system shall save receipt, receiving representative, timestamp, Completed transfer, Fulfilled reservation and request, the receiving department, custody and location of the received reserved units, and their linked life-cycle event as one operation; untransferred source units and their custody shall remain unchanged.
FR-8.14: The system shall prevent repeated receipt confirmation from changing quantities, custody, location, or history more than once.
FR-8.15: The system shall allow authorized Facilities personnel to record unsuccessful delivery attempts and revised delivery arrangements for an In Transit transfer, including reason, responsible user, and timestamp.
FR-8.16: The system shall keep an unsuccessful delivery In Transit with its reservation Active until a successful receipt or an authorized resolution; it shall not automatically return the asset to available stock.
FR-8.17: The system shall allow an authorized user to correct a recorded delivery discrepancy with a reason and supporting details while retaining the original discrepancy in history.
FR-8.18: The system shall allow cancellation of an unconfirmed dispatch, delivery-attempt entry, or receipt form without changing transfer records.
FR-8.19: The system shall deny unauthorized transfer access or updates and display a message when no accessible transfer exists.
FR-8.20: The system shall preserve previous request, reservation, quantities, transfer, receipt, custody, location, and history records if a related save operation fails and display an appropriate error.
FR-8.21: The system shall block dispatch when the recorded asset condition or active maintenance record makes the asset ineligible for transfer and require authorized resolution without silently releasing the reservation.
4.9 Asset Life Cycle Tracking
4.9.1 Description and Priority
This feature allows authorized Asset Custodians to view asset history, record life-cycle events, and update permitted asset states. The history covers acquisition, allocation, utilization, inspection, maintenance, repair, transfer, refurbishment, donation, recycling, retirement, and disposal. It preserves earlier records and links controlled actions to their approved workflows.
Priority: High (Must Have)
4.9.2 Stimulus Response Sequences
View Asset Life Cycle History
The Asset Custodian selects a registered asset and chooses View Life-Cycle History. The system checks access and displays dated events in chronological order, including the responsible user and recorded changes. If only registration exists, the system displays it and states that no later events are recorded.
Record Asset Life Cycle Event
The Asset Custodian selects Record Life-Cycle Event, enters the event type, date, description, and supporting details, and submits the form. The system validates the input and required authorization, saves the event, and displays confirmation. For example, an inspection of a laboratory monitor becomes a dated entry in its history.
Update Asset Life Cycle Status
The Asset Custodian selects Update Life-Cycle Status and chooses a permitted state. The system validates the transition, checks approvals and conflicting reservations or transfers, and saves the status and history entry together. Transfer completion and custody changes must use the transfer workflow; a manual status update cannot bypass receipt confirmation.
Request and Review End of Life Action
The custodian proposes a donation, recycling, retirement or disposal action with supporting details. An independently authorized Approver reviews and confirms approval or rejection. The system records the decision without changing asset state; completion is recorded later through the life-cycle event workflow using that approval reference.
4.9.3 Functional Requirements
FR-9.1: The system shall allow authorized Asset Custodians to view the life-cycle history of registered assets within their assigned authority.
FR-9.2: The system shall display recorded life-cycle events in chronological order, including event type, event date, description, responsible user, and recorded status, condition, custody, or location changes where applicable.
FR-9.3: The system shall display the registration event and indicate that no later events exist when an asset has no subsequent history.
FR-9.4: The system shall allow authorized Asset Custodians to record acquisition, allocation, utilization, inspection, maintenance, repair, transfer, refurbishment, donation, recycling, retirement, and disposal events.
FR-9.5: The system shall require an existing asset identifier, event type, event date, and description before saving a manually entered life-cycle event.
FR-9.6: The system shall reject missing or invalid event information and identify the fields requiring correction.
FR-9.7: The system shall assign each saved event a unique identifier and record the submitting user and system recording timestamp separately from the supplied event date.
FR-9.8: The system shall append new events without overwriting or deleting previously recorded life-cycle events.
FR-9.9: The system shall allow authorized Asset Custodians to view the current asset state and select only state changes permitted by the applicable workflow.
FR-9.10: The system shall reject an invalid state transition without changing the current asset state or its history.
FR-9.11: The system shall verify the required approval before recording donation, recycling, retirement, or disposal as completed.
FR-9.12: The system shall prevent manual life-cycle entry or status updates from completing a transfer or changing custody and location before receipt confirmation through the transfer workflow.
FR-9.13: The system shall prevent a state update from making an asset unavailable while it has an active reservation or pending transfer unless the relevant workflow has first resolved that commitment.
FR-9.14: The system shall save a permitted state change and its associated history event as one operation, preserving the previous state and history if saving fails.
FR-9.15: The system shall link maintenance, repair, and completed transfer events to their originating records so that the same completed operation is not recorded twice.
FR-9.16: The system shall prevent unauthorized access to life-cycle histories and unauthorized creation of events or status updates.
FR-9.17: The system shall allow cancellation before submission without saving an event or changing asset state.
FR-9.18: The system shall display confirmation after a successful event entry or status update and display an error without partial changes if the asset cannot be retrieved or the save fails.
FR-9.19: The system shall retain a correction as a new event linked to the original event, with correction reason, responsible user, and timestamp, without overwriting the original history.
FR-9.20: The system shall allow an Asset Custodian to propose a donation, recycling, retirement or disposal action with an asset reference and supporting reason for review by an independently authorized Approver.
FR-9.21: The system shall allow the assigned independent Approver to approve or reject an eligible proposed end-of-life action, recording the decision, reason, reviewer and timestamp without executing the action.
FR-9.22: The system shall prevent self-approval and completion of an end-of-life action without its matching approval reference, and preserve the previous proposal and asset state if validation or saving fails.
4.10 Maintenance and Repair Tracking
4.10.1 Description and Priority
This feature allows authorized Asset Custodians to report defects and request inspections, and authorized Maintenance Staff to record repair actions, costs, progress, and asset condition after service. Maintenance records are linked to the asset life-cycle history. A completed repair does not by itself make an asset available for reservation or transfer.
Priority: High (Must Have)
4.10.2 Stimulus Response Sequences
Report Asset Defect
The Asset Custodian selects Report Defect for a registered asset and enters the description, severity, discovery date, and supporting information. The system validates and saves the report, sets the maintenance status to Defect Reported, confirms submission, and notifies Maintenance Staff. For example, a monitor that no longer powers on can be reported for assessment.
Request Asset Inspection
The Asset Custodian selects Request Inspection and enters the reason, urgency, preferred date, and supporting details. The system checks for an active inspection request for the asset. If none exists, it saves the request as Inspection Requested and notifies Maintenance Staff; otherwise, it displays the existing request and prevents duplication.
Record Asset Repair
Maintenance Staff select the relevant maintenance record and enter repair actions, outcome, date, costs, and supporting information. The system validates and saves the record, links it to the life-cycle history, and sets Repair Completed for a successful repair or Further Repair Required for an unsuccessful or incomplete repair.
Track Maintenance Status and Update Asset Condition
Maintenance Staff view a maintenance record and select Update Maintenance Status. The system displays the current progress, condition, and permitted updates. Staff submit the new status, condition, and supporting notes. The system validates and saves the update and its history entry. Availability is restored only through an authorized asset-state update after the condition supports reuse.
4.10.3 Functional Requirements
FR-10.1: The system shall allow authorized Asset Custodians to report defects for registered assets within their assigned authority.
FR-10.2: The system shall record the asset identifier, defect description, severity, discovery date, reporting user, and supplied supporting information for each defect report.
FR-10.3: The system shall validate required defect fields and reject incomplete or invalid submissions with field-specific messages.
FR-10.4: The system shall save a valid defect report with maintenance status Defect Reported, display confirmation, and notify authorized Maintenance Staff.
FR-10.5: The system shall allow authorized Asset Custodians to request an asset inspection by entering the reason, urgency, preferred inspection date, and optional supporting details.
FR-10.6: The system shall reject an invalid inspection request and identify the information requiring correction.
FR-10.7: The system shall prevent a duplicate active inspection request for the same asset and display the existing request reference.
FR-10.8: The system shall save a valid inspection request with maintenance status Inspection Requested, display confirmation, and notify authorized Maintenance Staff.
FR-10.9: The system shall allow authorized Maintenance Staff to view maintenance records, current status, and recorded asset condition for assets within their assigned authority.
FR-10.10: The system shall allow authorized Maintenance Staff to record repair descriptions, actions performed, repair date, repair outcome, cost, currency, and supporting information against an existing maintenance record.
FR-10.11: The system shall reject a repair record with missing mandatory information, an invalid date, or a negative or nonnumeric cost.
FR-10.12: The system shall set maintenance status to Repair Completed when a successful repair is recorded and to Further Repair Required when the repair is unsuccessful or incomplete.
FR-10.13: The system shall allow authorized Maintenance Staff to update maintenance progress and asset condition, including recording In Progress while work continues.
FR-10.14: The system shall validate maintenance-status changes against the applicable workflow and require supporting notes for a condition update.
FR-10.15: The system shall link saved defect reports, inspection requests, repair records, and progress or condition changes to the corresponding asset life-cycle history.
FR-10.16: The system shall retain previous maintenance events and record the responsible user and timestamp for each new maintenance or condition update.
FR-10.17: The system shall save a maintenance update, associated condition change, and linked history event as one operation and preserve the previous records if saving fails.
FR-10.18: The system shall prevent a maintenance-status update from automatically releasing an asset for reservation or transfer; availability shall require a permitted asset-state update after service.
FR-10.19: The system shall deny maintenance access and updates outside the user's assigned permissions.
FR-10.20: The system shall allow cancellation before submission without saving changes and display confirmation or an appropriate retrieval or save error after a submitted operation.
4.11 Sustainability Recommendations
4.11.1 Description and Priority
This feature allows authorized Sustainability Officers to generate, review, accept, or reject AI-assisted recommendations for reuse, transfer, repair, refurbishment, donation, recycling, or retirement. Recommendations use available asset condition, age, usage, maintenance, cost, and environmental information. Explanations and data limitations support human review; accepting a recommendation records a decision and routes any required approval rather than executing the action.
Priority: Medium (Should Have)
4.11.2 Stimulus Response Sequences
Generate Sustainability Recommendations
The Sustainability Officer selects a registered asset and chooses Generate Sustainability Recommendations. The system checks permission and available information, requests analysis from the AI Recommendation Service, and displays the suggested action with an explanation. For example, the service may suggest repairing a monitor when its recorded condition and repair estimate support continued use.
Review Sustainability Recommendations
The Sustainability Officer selects an existing recommendation. The system displays the suggested action, supporting asset information, available cost and environmental estimates, and any confidence or data limitations. Viewing a recommendation leaves the asset record unchanged. If information is insufficient, the officer asks an authorized custodian to correct the asset record before requesting a new analysis.
Accept or Reject Sustainability Recommendations
The Sustainability Officer reviews the recommendation and selects Accept or Reject. The system requests confirmation and, for rejection, a reason. Before saving, it rechecks that the recommendation is current and undecided. It records the decision, officer, and timestamp and forwards an accepted action for any required approval. The asset state remains unchanged until the authorized operational workflow implements the action.
4.11.3 Functional Requirements
FR-13.1: The system shall allow authorized Sustainability Officers to request sustainability recommendations for registered assets they have permission to access.
FR-13.2: The system shall retrieve available asset condition, age, usage history, maintenance and repair history, availability, and relevant cost and environmental information for analysis.
FR-13.3: The system shall validate that sufficient asset information is available and identify missing information when a recommendation cannot be generated.
FR-13.4: The system shall send only the asset information needed for analysis to the AI Recommendation Service.
FR-13.5: The system shall display the recommended action and a human-readable explanation identifying the asset information that supports it.
FR-13.6: The system shall support recommendations for retention for reuse, transfer, repair, refurbishment, donation, component recovery, recycling, retirement or disposal as a final option without automatically executing the suggested action.
FR-13.7: The system shall display a confidence value when supplied by the AI service and explicitly indicate when confidence information is unavailable.
FR-13.8: The system shall label financial and environmental benefits as estimates when they depend on assumptions and display the available units, data sources, and assumptions; unavailable values shall be identified rather than invented.
FR-13.9: The system shall store each generated recommendation with a unique identifier, asset identifier, generation timestamp, and reference to the asset information used in the analysis.
FR-13.10: The system shall allow authorized Sustainability Officers to retrieve and review saved recommendations without changing the asset state or its operational records.
FR-13.11: The system shall display an appropriate message when no recommendation exists or the selected recommendation cannot be retrieved.
FR-13.12: The system shall allow a new recommendation to be requested after authorized corrections to asset information without overwriting the previous recommendation or its recorded decision.
FR-13.13: The system shall allow authorized Sustainability Officers to accept or reject an undecided recommendation after explicit confirmation.
FR-13.14: The system shall require a reason before saving a rejection and preserve the asset's existing state after the decision.
FR-13.15: The system shall record the decision, responsible officer, timestamp, and rejection reason where applicable.
FR-13.16: The system shall recheck recommendation status and relevant asset information before saving a decision and prevent decisions on an already processed or outdated recommendation.
FR-13.17: The system shall forward accepted recommendations for any approvals required by the proposed action and prevent recommendation acceptance from bypassing authorization or changing asset state automatically.
FR-13.18: The system shall display an appropriate error if the AI service fails and allow retry or manual assessment through authorized existing workflows without generating a false recommendation.
FR-13.19: The system shall prevent unauthorized generation, access, or decisions on sustainability recommendations.
FR-13.20: The system shall allow cancellation before generation is submitted or a decision is confirmed without applying the cancelled operation, and display confirmation after a saved decision.
4.12 AI Based Resource Matching
4.12.1 Description and Priority
Authorized Department Representatives can generate, review, and regenerate ranked matches between an open departmental request and accessible published assets. AI compares meaning and suitability using available request, asset, cost, and sustainability information. Matches remain advisory and cannot reserve an asset or approve a request.
Priority: Medium (Should Have)
4.12.2 Stimulus Response Sequences
Generate AI Resource Matches
The representative selects an eligible open request and Generate AI Matches. The system validates information, gathers accessible published assets, and asks the AI matching module to compare candidates. It displays ranked assets, compatibility scores, and explanations. For example, a request for a display screen may match a listing described as a monitor.
Review AI Resource Matches
The representative selects a recommended asset. The system rechecks permission and current availability and displays specifications, condition, quantity, location, score, and explanation. The representative can return to the list or link a suitable asset through the resource-request workflow.
Regenerate AI Resource Matches
The representative saves any permitted request corrections and selects Regenerate Matches. The system uses current request and asset information to produce a new result set without overwriting previous sets or automatically replacing a selected asset. If AI fails, the representative can search and filter manually.
4.12.3 Functional Requirements
FR-12.1: The system shall allow authorized Department Representatives to generate resource matches for their accessible Pending Approval requests.
FR-12.2: The system shall retrieve the current request category, purpose, specifications, quantity, preferred condition, urgency, location, and required date for matching.
FR-12.3: The system shall consider only published assets the representative is permitted to view and use their current availability and unreserved quantity.
FR-12.4: The system shall validate required request information and identify missing information before generating matches.
FR-12.5: The system shall compare requests and asset descriptions semantically so that different wording can identify functionally suitable assets.
FR-12.6: The system shall evaluate category compatibility, purpose, specifications, quantity, condition, location, urgency, required date, and available transfer, repair, and sustainability information.
FR-12.7: The system shall exclude assets that do not meet required quantity or mandatory specifications from recommendations presented as suitable.
FR-12.8: The system shall rank suitable candidates and display each asset's identifier, compatibility score, and a human-readable explanation of the factors influencing its rank.
FR-12.9: The system shall display compatibility scores on a stated 0 to 100 scale, with 100 representing the strongest compatibility on that scale, separately from AI confidence; absent confidence shall be identified as unavailable.
FR-12.10: The system shall identify missing cost or environmental inputs and label assumption-based benefits as estimates with available units and sources.
FR-12.11: The system shall store each result set with a unique identifier, generation timestamp, request reference, and the input versions or snapshot used for matching.
FR-12.12: The system shall allow representatives to review saved result sets and the corresponding permitted asset details without modifying asset or request records.
FR-12.13: The system shall recheck permission, publication, and available quantity when a recommended asset is selected and identify an outdated or unavailable match.
FR-12.14: The system shall allow regeneration using the latest saved request and currently available assets while preserving prior result sets.
FR-12.15: The system shall prevent generation or regeneration from automatically changing a selected asset, reserving quantity, approving a request, or creating a transfer.
FR-12.16: The system shall allow a suitable recommended asset to be selected through the resource-request update workflow, subject to its eligibility and validation rules.
FR-12.17: The system shall display a clear message if no suitable matches exist and allow manual search or later regeneration.
FR-12.18: The system shall display an appropriate failure message when the AI matching module fails and allow retry or manual search without presenting failed results as a new successful result set.
FR-12.19: The system shall allow generation, regeneration, or review to be cancelled before submission without applying the cancelled operation or replacing previous results.
FR-12.20: The system shall deny unauthorized matching requests or result access and preserve prior result sets and selected request details if saving generated results fails.
4.13 Reporting
4.13.1 Description and Priority
Authorized users can generate operational and sustainability reports from records within their access scope. Conventional totals remain available without AI. Optional AI summaries explain an existing report and remain subject to human review before export or sharing.
Priority: High (Must Have) for conventional operational reports; Medium (Should Have) for supported sustainability estimates; Low (Could Have) for generative AI summaries.
4.13.2 Stimulus Response Sequences
Generate Operational Report
The user selects a report type, department and date range. The system validates permission and filters and displays totals and detailed records for available assets, requests, approvals, reservations, transfers, maintenance, custody changes or asset states. The user may export the permitted result as CSV.
Generate Sustainability Report
The Sustainability Officer, Finance Officer or other authorized user selects a reporting period. The system calculates reuse, avoided purchases, recorded costs, waste diversion, asset life extension and carbon estimates using documented available data and the definitions in Section 6.3. Missing evidence is marked unavailable rather than counted as zero.
Generate AI Report Summary
The user selects a successfully generated report and requests a summary. The system submits only authorized report content to the AI service and displays the draft with its report reference and limitations. The user reviews, edits or rejects it. For example, a summary can describe monitor reuse while retaining the exact computed totals.
4.13.3 Functional Requirements
FR-15.1: The system shall allow authorized users to select an operational report type and a permitted department and date range.
FR-15.2: The system shall provide operational reports for available assets, requests and reservations, approval decisions, completed and open transfers, maintenance history, custody changes, and asset states.
FR-15.3: The system shall validate date ranges and department permissions before retrieving records or generating a report.
FR-15.4: The system shall limit report rows, totals and sensitive fields to the requesting user's role and departmental scope, including financial fields.
FR-15.5: The system shall calculate conventional report totals from stored operational records without requiring an AI service.
FR-15.6: The system shall identify each generated report with its type, filters, generation timestamp and data cutoff so that users can interpret its scope.
FR-15.7: The system shall display an explicit no-data result when no eligible records exist and distinguish this from a retrieval or calculation failure.
FR-15.8: The system shall allow authorized users to export the displayed permitted report as CSV with its column names and filter or period information.
FR-15.9: The system shall provide sustainability reports using the reuse, savings, waste diversion, asset life extension and carbon definitions in Section 6.3 when their required data are available.
FR-15.10: The system shall label estimated benefits with units, source inputs, assumptions and data limitations, and identify a missing input or undefined ratio as unavailable rather than inventing a value.
FR-15.11: The system shall allow authorized users to request an optional AI summary of a generated report using only the report data they are permitted to access.
FR-15.12: The system shall label an AI report summary as a draft and associate it with the exact source report and its generation timestamp.
FR-15.13: The system shall allow the user to review, edit, accept or reject an AI summary before exporting that summary, and prevent an AI summary from modifying operational records or computed totals.
FR-15.14: The system shall display an error when AI summarization fails and retain access to the original conventional report and CSV export.
FR-15.15: The system shall prevent an export or summary from exposing records or financial details outside the user's current permission scope.
FR-15.16: The system shall preserve source records if report generation or export fails and display an error without presenting a failed result as a complete report.
FR-15.17: The system shall record report generation, export and AI-summary decisions with the responsible user, timestamp and report reference.
4.14 Authentication and Access Control
4.14.1 Description and Priority
Users authenticate before accessing protected campus functions. The system enforces role and departmental scope for every operation, supports logout and inactivity expiry, and allows System Administrators to manage accounts and permissions and review security logs. Authentication does not automatically grant asset-custodian or approval authority.
Priority: High (Must Have)
4.14.2 Stimulus Response Sequences
Log In
The user submits account credentials. The system validates the active account, establishes a protected session, and shows only functions allowed by the assigned roles. Invalid credentials produce a generic error without revealing whether an account exists.
Log Out
The user selects Log Out. The system invalidates the session and returns to the login screen. A session also expires after 15 minutes of inactivity, as required by NFR-17.
Manage User Accounts and Roles
The System Administrator selects an account or creates a new one, specifies its active status, roles and departmental scope, and confirms. The system validates authority and values, saves the change with an audit record, and applies revised access immediately.
Review Security Audit Log
The System Administrator selects event and date filters. The system displays permitted login, access, permission-change and critical-operation events with their users and timestamps. For example, the administrator can review an attempted access to another department's assets.
4.14.3 Functional Requirements
FR-1.1: The system shall require a valid active user account and successful authentication before granting access to protected functions.
FR-1.2: The system shall validate submitted credentials without displaying or storing plaintext passwords, in accordance with NFR-16.
FR-1.3: The system shall display a generic authentication failure message for invalid credentials or inactive accounts without identifying which credential was incorrect.
FR-1.4: The system shall establish an authenticated session associated with the user's identity, assigned roles and departmental scope after successful login.
FR-1.5: The system shall enforce role and departmental permissions when displaying protected information and immediately before committing an operation, including calls made through the assistant or AI services.
FR-1.6: The system shall allow a logged-in user to log out and invalidate the session so that subsequent protected requests require authentication.
FR-1.7: The system shall expire a session after 15 minutes of inactivity and require authentication again before resuming protected functions.
FR-1.8: The system shall allow authorized System Administrators to create and deactivate accounts and assign or change supported roles and departmental scopes.
FR-1.9: The system shall validate account identifier uniqueness, mandatory account details, roles and departmental scope before saving account changes.
FR-1.10: The system shall record the administrator, affected account, previous and new role or status values, reason where supplied, and timestamp for account or permission changes.
FR-1.11: The system shall prevent ordinary users from assigning themselves roles or widening their departmental permissions.
FR-1.12: The system shall apply deactivation and permission reductions to active sessions so that removed access cannot be used for later operations.
FR-1.13: The system shall allow authorized System Administrators to view and filter security audit events by date, user and event type without modifying recorded events.
FR-1.14: The system shall record successful and failed login attempts, logout or expiry, denied access, account changes and security-sensitive operations with timestamps and responsible identities where known.
FR-1.15: The system shall prevent account changes from leaving the system without an active System Administrator.
FR-1.16: The system shall preserve the previous account and permission configuration when validation or saving fails and display an appropriate error.
FR-1.17: The system shall prevent user-facing messages and audit views from revealing passwords, session secrets or AI-service credentials.
4.15 LLM Powered Assistant
4.15.1 Description and Priority
An optional natural-language assistant helps authenticated users find assets, ask record or policy questions, navigate system functions, and prepare resource requests. It retrieves only authorized information and passes any confirmed operation to the existing validated workflow. The core system remains usable without the assistant.
Priority: Low (Could Have)
4.15.2 Stimulus Response Sequences
Search Assets Using Natural Language
The user asks for an asset in ordinary language. The assistant interprets the request, asks for clarification when needed, searches authorized current listings, and returns referenced results. For example, “Find two monitors for our teaching lab” can open the same permitted search or matching results as the normal interface.
Ask Asset or Policy Questions
The user asks about an asset, request, transfer or approved campus procedure. The system retrieves permitted records or approved policy material and returns an answer with source references and uncertainty. If no supporting information exists, it says so and offers normal navigation.
Prepare and Submit a Resource Request
The assistant gathers the required request fields and displays a draft. The user reviews and explicitly confirms submission. The system rechecks authority and field validity and submits the draft through Resource Requests as Pending Approval, without reserving an asset or approving a transfer.
4.15.3 Functional Requirements
FR-14.1: The system shall allow authenticated authorized users to enter natural-language questions and requests for asset search, record information, policy guidance and system navigation.
FR-14.2: The system shall limit assistant retrieval, answers and tool operations to the user's current role and departmental scope.
FR-14.3: The system shall interpret a natural-language asset search and use the existing search or matching functionality to return accessible current listings.
FR-14.4: The system shall ask the user to clarify missing or ambiguous information rather than choosing an unsupported asset, department or requested action.
FR-14.5: The system shall answer asset-history, request-status and transfer-status questions using authorized stored records and include references identifying the supporting records.
FR-14.6: The system shall answer policy questions only from approved available policy material and identify the source used.
FR-14.7: The system shall identify unsupported answers, missing information or uncertainty and avoid inventing asset availability, approval decisions, policy rules or sustainability values.
FR-14.8: The system shall allow the user to prepare a resource request by collecting the mandatory request fields defined under FR-5.
FR-14.9: The system shall display all proposed request fields, department and selected asset if any and require explicit user confirmation before submission.
FR-14.10: The system shall revalidate permission, current asset information and request fields and execute confirmed request submission through FR-5 as Pending Approval without automatically reserving or transferring an asset.
FR-14.11: The system shall allow the user to correct or cancel a proposed request before confirmation without saving it.
FR-14.12: The system shall prevent natural-language instructions, retrieved asset descriptions or policy documents from bypassing access controls, required approvals or confirmation.
FR-14.13: The system shall provide links or navigation to the normal system screens for supported tasks and when the user chooses manual operation.
FR-14.14: The system shall display an assistant-service error and retain access to normal search, record viewing and request forms if the LLM service is unavailable.
FR-14.15: The system shall avoid sending credentials or unrelated restricted university records to the LLM service and record the responsible user and resulting request reference for a confirmed assistant operation.
FR-14.16: The system shall prevent repeated confirmation of the same assistant draft from creating duplicate resource requests.

Section 7

7.9 Asset Life Cycle Tracking
Rules: History is append-only. Corrections reference the original event and preserve it. State updates must use the vocabulary in Section 6.2.1 and cannot bypass approvals or change transfer custody before receipt. A retired asset may proceed to an approved donation, recycling, or disposal workflow; a completed end-of-life event cannot be reversed by a generic edit.

Example: View a monitor's inspection history, append a repair event, or request a permitted status update.
7.9.1 View Asset Life-Cycle History
Use Case ID: UC-10
Use Case Name: View Asset Life-Cycle History
Related Requirement: FR-9: Asset Life-Cycle Tracking
Detailed Requirements: FR-9.1 through FR-9.3; FR-9.16; FR-9.18
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to view the complete history of a registered asset, including its acquisition, allocation, inspections, maintenance, repairs, transfers, refurbishment, donation, recycling, retirement, and disposal.
Preconditions: The Asset Custodian is logged into the system, has permission to view the asset's history, and the asset is already registered in the system.
Trigger: The Asset Custodian selects View Life-Cycle History for a registered asset.
Postconditions: The system displays the selected asset's complete life-cycle history in chronological order without modifying any stored information.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects an asset from the list.
4. The Asset Custodian clicks View Life-Cycle History.
5. The system retrieves all recorded life-cycle events associated with the selected asset.
6. The system displays the asset's history, including event types, dates, descriptions, and relevant status changes.
7. The Asset Custodian reviews the asset's life-cycle history.
Alternative Flows
A1 No Life-Cycle Events Recorded
At step 5, the system finds no recorded life-cycle events beyond the asset's initial registration.
The system displays the available registration information and indicates that no additional life-cycle events have been recorded.
Exception Flows
E1 Asset Not Found
At step 5, the selected asset no longer exists or cannot be retrieved.
The system displays an error message and allows the Asset Custodian to return to the asset list.
E2 Unauthorized Access
The Asset Custodian attempts to view the history of an asset they do not have permission to access.
The system denies access and displays an appropriate error message.
7.9.2 Record Asset Life-Cycle Event
Use Case ID: UC-11
Use Case Name: Record Asset Life-Cycle Event
Related Requirement: FR-9: Asset Life-Cycle Tracking
Detailed Requirements: FR-9.4 through FR-9.8; FR-9.11 through FR-9.12; FR-9.15 through FR-9.18; FR-9.19
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to record important events throughout an asset's life cycle, including acquisition, allocation, inspection, maintenance, repair, transfer, refurbishment, donation, recycling, retirement, and disposal.
Preconditions: The Asset Custodian is logged into the system, has permission to record life-cycle events, and the asset is already registered in the system.
Trigger: The Asset Custodian selects Record Life-Cycle Event.
Postconditions: The new life-cycle event is successfully recorded and stored in the asset's history. The Asset Custodian receives a confirmation pop-up notification indicating that the event has been recorded successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects an asset from the list.
4. The Asset Custodian clicks Record Life-Cycle Event.
5. The system displays a form for entering the event details.
6. The Asset Custodian selects the event type and enters the relevant information, including the event date, description, and any supporting details.
7. The Asset Custodian submits the event information.
8. The system validates the entered information and checks that any required approvals have been completed.
9. The system saves the new event in the asset's life-cycle history.
10. The system displays a confirmation pop-up indicating that the event has been recorded successfully.
Alternative Flows
A1 Event Recording Cancelled
Before submitting the event information, the Asset Custodian cancels the operation.
The system returns to the asset details page without saving the event.
A2 Correction of an Earlier Event
At step 6, the custodian identifies an erroneous historical entry, supplies the original event reference and correction reason, and submits a corrective event. The system appends the correction without altering the original entry.
Exception Flows
E1 Missing or Invalid Information
At step 8, the system detects missing or invalid event information.
The system displays an error message identifying the issue.
The Asset Custodian corrects the information and resubmits the form.
E2 Unauthorized Action
The Asset Custodian attempts to record an event without the required permissions.
The system denies the operation and displays an appropriate error message.
E3 Required Approval Missing
At step 8, the system determines that the selected event requires approval that has not yet been granted.
The system prevents the event from being recorded as completed and informs the Asset Custodian that authorization is required.
E4 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.9.3 Update Asset Life-Cycle Status
Use Case ID: UC-12
Use Case Name: Update Asset Life-Cycle Status
Related Requirement: FR-9: Asset Life-Cycle Tracking
Detailed Requirements: FR-9.9 through FR-9.14; FR-9.16 through FR-9.18
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to update a registered asset to a permitted state defined in Section 6.2.1. Approval, maintenance, reservation, and transfer workflow rules determine which transitions are allowed.
Preconditions: The Asset Custodian is logged into the system, has permission to update the asset's life-cycle status, and the asset is already registered in the system.
Trigger: The Asset Custodian selects Update Life-Cycle Status.
Postconditions: The asset's life-cycle status is successfully updated and stored in the system. The status change is recorded in the asset's life-cycle history, and the Asset Custodian receives a confirmation pop-up notification.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects an asset from the list.
4. The Asset Custodian clicks Update Life-Cycle Status.
5. The system displays the asset's current life-cycle status and available status options.
6. The Asset Custodian selects a permitted state from Section 6.2.1 and provides the required details. Transfer completion and custody changes use the transfer workflow.
7. The Asset Custodian submits the updated status.
8. The system validates the selected transition, checks required approvals, and confirms that active reservations or transfers have been resolved before an unavailable state can be applied.
9. The system saves the permitted asset state and its history event as one operation. A failed save preserves the previous records.
10. The system displays a confirmation pop-up indicating that the asset's status has been updated successfully.
Alternative Flows
A1 Status Update Cancelled
Before submitting the updated status, the Asset Custodian cancels the operation.
The system returns to the asset details page without changing the asset's current status.
Exception Flows
E1 Invalid Status Change
At step 8, the system determines that the selected status change is not permitted.
The system displays an error message and asks the Asset Custodian to select a valid status.
E2 Unauthorized Status Update
The Asset Custodian attempts to update an asset's status without the required permissions.
The system denies the operation and displays an appropriate error message.
E3 Required Approval Missing
At step 8, the system determines that the selected status change requires approval that has not been granted.
The system prevents the status update and informs the Asset Custodian that approval is required before proceeding.
E4 Outstanding Reservation or Transfer
At step 8, a state change would invalidate an active reservation or pending transfer. The system blocks the change and requires the relevant authorized workflow to resolve the commitment first.
E5 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.9.4 Propose and Review End of Life Action
Use Case ID: UC-49
Use Case Name: Propose and Review End of Life Action
Related Requirement: FR-9 Asset Life Cycle Tracking
Detailed Requirements: FR-9.11; FR-9.20 through FR-9.22
Primary Actor: Authorized Approver
Supporting Actor: Asset Custodian
Goal: Record independent authorization for a proposed end-of-life action without executing it.
Preconditions: The asset exists. The proposing custodian and reviewing Approver are authenticated, assigned to the relevant asset, and are different users.
Trigger: The custodian submits an end-of-life proposal for review.
Postconditions: Approval or rejection is recorded with traceable responsibility; the asset remains unchanged until approved action completion is recorded.
Failure Postconditions: The previous request, proposal, asset and allocation records remain unchanged if authorization, validation or saving fails.
Main Success Scenario
1. The custodian selects the asset and proposes donation, recycling, retirement or disposal with a reason and supporting details.
2. The system validates authority, asset eligibility and outstanding reservations or transfers and records the proposal for independent review.
3. The assigned Approver opens the proposal and reviews its evidence and current asset commitments.
4. The Approver selects Approve or Reject, provides a reason and confirms.
5. The system rechecks independent authority, current proposal status and asset eligibility, then saves the decision, reviewer and timestamp.
6. The system informs the custodian of the result and exposes an approved reference for subsequent event recording; it does not execute the physical action or change custody or asset state.
Alternative Flows
A1 Review Abandoned
Before step 4, the reviewer cancels; the proposal remains awaiting a decision.
A2 Proposal Rejected
At step 4, the reviewer selects Reject. The system records the reason and blocks completion based on that proposal.
Exception Flows
E1 Self Decision or Missing Authority
At step 2 or 5, authority fails or proposer and reviewer are the same user. The system blocks the operation.
E2 Commitment or Prior Decision Conflict
The asset has unresolved reservations or transfers, or the proposal already has a decision. The system blocks the conflicting action and requires authorized resolution.
E3 Save Failure
The system reports failure and preserves the previous proposal and asset state.
7.10 Maintenance and Repair Tracking
Rules: Maintenance status and asset availability are separate. Allowed progress includes Defect Reported or Inspection Requested to In Progress, then Repair Completed or Further Repair Required; Further Repair Required can return to In Progress. Repair completion does not automatically release an asset for reuse.

Example: Report a monitor that does not power on, request inspection, and record the eventual repair outcome and cost.
7.10.1 Report Asset Defect
Use Case ID: UC-13
Use Case Name: Report Asset Defect
Related Requirement: FR-10: Maintenance and Repair Tracking
Detailed Requirements: FR-10.1 through FR-10.4; FR-10.15 through FR-10.20
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to report defects or issues with registered campus assets so that they can be inspected and repaired by authorized maintenance staff.
Preconditions: The Asset Custodian is logged into the system, has permission to report asset defects, and the asset is already registered in the system.
Trigger: The Asset Custodian selects Report Defect.
Postconditions: The defect report is successfully recorded and stored in the system. The asset's maintenance status is updated to indicate that an issue has been reported. The Asset Custodian receives a confirmation pop-up notification, and the maintenance staff are notified of the reported defect.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects the asset with the defect.
4. The Asset Custodian clicks Report Defect.
5. The system displays a defect reporting form.
6. The Asset Custodian enters the defect description, severity, date of discovery, and any relevant supporting information.
7. The Asset Custodian submits the defect report.
8. The system validates the entered information.
9. The system saves the defect report and updates the asset's maintenance status to Defect Reported.
10. The system displays a confirmation pop-up and notifies the maintenance staff about the reported defect.
Alternative Flows
A1 Defect Report Cancelled
Before submitting the defect report, the Asset Custodian cancels the operation.
The system returns to the asset details page without saving the defect report.
Exception Flows
E1 Missing or Invalid Information
At step 8, the system detects missing or invalid defect information.
The system displays an error message identifying the issue.
The Asset Custodian corrects the information and resubmits the report.
E2 Unauthorized Access
The Asset Custodian attempts to report a defect for an asset they do not have permission to manage.
The system denies the operation and displays an appropriate error message.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.10.2 Request Asset Inspection
Use Case ID: UC-14
Use Case Name: Request Asset Inspection
Related Requirement: FR-10: Maintenance and Repair Tracking
Detailed Requirements: FR-10.5 through FR-10.8; FR-10.15 through FR-10.20
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to request an inspection of a registered campus asset to assess its condition, identify potential defects, and determine whether maintenance or repair is required.
Preconditions: The Asset Custodian is logged into the system, has permission to request asset inspections, and the asset is already registered in the system.
Trigger: The Asset Custodian selects Request Inspection.
Postconditions: The inspection request is successfully recorded and stored in the system. The asset's maintenance status is updated to Inspection Requested. The Asset Custodian receives a confirmation pop-up notification, and the maintenance staff are notified of the new inspection request.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects the asset requiring inspection.
4. The Asset Custodian clicks Request Inspection.
5. The system displays an inspection request form.
6. The Asset Custodian enters the reason for inspection, urgency, preferred inspection date, and any relevant supporting information.
7. The Asset Custodian submits the inspection request.
8. The system validates the entered information.
9. The system saves the inspection request and updates the asset's maintenance status to Inspection Requested.
10. The system displays a confirmation pop-up and notifies the maintenance staff about the inspection request.
Alternative Flows
A1 Inspection Request Cancelled
Before submitting the inspection request, the Asset Custodian cancels the operation.
The system returns to the asset details page without saving the inspection request.
A2 Inspection Already Requested
At step 4, the system detects that an active inspection request already exists for the selected asset.
The system informs the Asset Custodian that an inspection has already been requested and prevents duplicate submissions.
Exception Flows
E1 Missing or Invalid Information
At step 8, the system detects missing or invalid inspection request information.
The system displays an error message identifying the issue.
The Asset Custodian corrects the information and resubmits the request.
E2 Unauthorized Access
The Asset Custodian attempts to request an inspection for an asset they do not have permission to manage.
The system denies the operation and displays an appropriate error message.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.10.3 Record Asset Repair
Use Case ID: UC-15
Use Case Name: Record Asset Repair
Related Requirement: FR-10: Maintenance and Repair Tracking
Detailed Requirements: FR-10.9 through FR-10.12; FR-10.15 through FR-10.20
Primary Actor: Maintenance Staff
Goal: Allow authorized Maintenance Staff to record completed repairs on registered campus assets, including repair details, costs, and actions taken, to ensure accurate maintenance records and asset condition tracking.
Preconditions: The Maintenance Staff member is logged into the system, has permission to record repairs, and the asset is already registered in the system. The asset has undergone maintenance or repair.
Trigger: Maintenance Staff select Record Repair for a maintenance record.
Postconditions: The repair information is successfully recorded and stored in the system. The asset's maintenance history is updated, and its maintenance status is changed to Repair Completed. The Maintenance Staff member receives a confirmation pop-up notification indicating that the repair has been recorded successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Maintenance Staff member navigates to the Maintenance Management section.
2. The system displays a list of assets requiring maintenance or repair.
3. The Maintenance Staff member selects the asset that has been repaired.
4. The Maintenance Staff member clicks Record Repair.
5. The system displays a repair recording form.
6. Maintenance Staff enter repair description, actions performed, repair date, outcome, nonnegative cost and currency, and any supporting information.
7. The Maintenance Staff member submits the repair information.
8. The system rechecks permissions and validates the maintenance reference, required fields, repair date, outcome, and nonnegative numeric cost.
9. The system saves the repair record, linked life-cycle event, and Repair Completed status as one operation; unsuccessful outcomes instead use Further Repair Required.
10. The system displays a confirmation pop-up indicating that the repair has been recorded successfully.
Alternative Flows
A1 Repair Recording Cancelled
Before submitting the repair information, the Maintenance Staff member cancels the operation.
The system returns to the maintenance management page without saving the repair record.
A2 Repair Unsuccessful
At step 6, the Maintenance Staff member indicates that the repair was unsuccessful or incomplete.
The system records the repair attempt and updates the maintenance status to Further Repair Required instead of Repair Completed.
Exception Flows
E1 Missing or Invalid Information
At step 8, the system detects missing or invalid repair information.
The system displays an error message identifying the issue.
The Maintenance Staff member corrects the information and resubmits the form.
E2 Unauthorized Access
The Maintenance Staff member attempts to record a repair without the required permissions.
The system denies the operation and displays an appropriate error message.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.10.4 Track Maintenance Status and Update Asset Condition
Use Case ID: UC-16
Use Case Name: Track Maintenance Status and Update Asset Condition
Related Requirement: FR-10: Maintenance and Repair Tracking
Detailed Requirements: FR-10.9; FR-10.13 through FR-10.20
Primary Actor: Maintenance Staff
Goal: Allow authorized Maintenance Staff to monitor the maintenance progress of registered campus assets and update their condition after inspections, maintenance, or repairs to ensure accurate asset records.
Preconditions: The Maintenance Staff member is logged into the system, has permission to view and update maintenance records, and the asset is already registered in the system with an existing maintenance record.
Trigger: Maintenance Staff select Update Maintenance Status.
Postconditions: The asset's maintenance status and condition are successfully updated and stored in the system. The changes are recorded in the asset's maintenance history, and the Maintenance Staff member receives a confirmation pop-up notification.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Maintenance Staff member navigates to the Maintenance Management section.
2. The system displays a list of assets with existing maintenance records.
3. The Maintenance Staff member selects an asset from the list.
4. The system displays the asset's current maintenance status, condition, and maintenance history.
5. The Maintenance Staff member reviews the maintenance progress and clicks Update Maintenance Status.
6. The system displays the available maintenance status and asset condition options.
7. The Maintenance Staff member selects the updated maintenance status and asset condition and enters any relevant supporting information.
8. The Maintenance Staff member submits the updated information.
9. The system rechecks permissions, validates the permitted maintenance-status transition, and requires supporting notes for any condition change.
10. The system saves the maintenance and condition changes with the linked life-cycle event as one operation. Repair completion does not automatically make the asset available.
11. The system displays a confirmation pop-up indicating that the maintenance status and asset condition have been updated successfully.
Alternative Flows
A1 Maintenance Update Cancelled
Before submitting the updated information, the Maintenance Staff member cancels the operation.
The system returns to the maintenance management page without changing the asset's maintenance status or condition.
A2 Maintenance Still in Progress
At step 7, the Maintenance Staff member indicates that maintenance or repair is not yet completed.
The system updates the maintenance status to In Progress and retains the appropriate asset condition until further maintenance is completed.
Exception Flows
E1 Missing or Invalid Information
At step 9, the system detects missing or invalid maintenance information.
The system displays an error message identifying the issue.
The Maintenance Staff member corrects the information and resubmits the update.
E2 Unauthorized Access
The Maintenance Staff member attempts to update maintenance information without the required permissions.
The system denies the operation and displays an appropriate error message.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
7.11 Sustainability Recommendations
Rules: Recommendations are advisory. Acceptance records a decision and initiates any required approval; implementation uses the authorized operational workflow. Stale or processed recommendations cannot receive another decision. Assumption-based benefits are identified as estimates.

Example: Review an explained suggestion to repair a monitor and record acceptance while retaining required human approvals.
7.11.1 Generate Sustainability Recommendations
Use Case ID: UC-17
Use Case Name: Generate Sustainability Recommendations
Related Requirement: FR-13: Sustainability Recommendations
Detailed Requirements: FR-13.1 through FR-13.9; FR-13.12; FR-13.18 through FR-13.20
Primary Actor: Sustainability Officer
Supporting Actor: AI Recommendation Service
Goal: Allow the Sustainability Officer to generate AI-based recommendations on whether a registered campus asset should be reused, transferred, repaired, refurbished, donated, recycled, or retired based on its condition, usage history, and sustainability impact.
Preconditions: The Sustainability Officer is authenticated and authorized for a registered asset. The system checks information sufficiency during the use case.
Trigger: The Sustainability Officer selects Generate Sustainability Recommendations.
Postconditions: The AI generates sustainability recommendations for the selected asset, along with explanations supporting the suggested actions. The recommendations are displayed to the Sustainability Officer for review without automatically changing the asset's status.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The Sustainability Officer navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Sustainability Officer selects an asset from the list.
4. The Sustainability Officer clicks Generate Sustainability Recommendations.
5. The system retrieves the asset's relevant information, including its condition, age, maintenance history, and current availability.
6. The system sends the asset information to the AI Recommendation Service.
7. The AI analyzes the asset information and evaluates possible sustainability actions.
8. The AI generates a recommended action, such as reuse, transfer, repair, refurbishment, donation, recycling, or retirement, along with an explanation.
9. The system stores and displays the recommendation and explanation, available confidence information, and the assumptions and limitations of any cost or environmental estimates.
10. The Sustainability Officer reviews the generated recommendation.
Alternative Flows
A1 Recommendation Generation Cancelled
Before generating the recommendation, the Sustainability Officer cancels the operation.
The system returns to the asset details page without generating or applying any recommendations.
Exception Flows
E1 Insufficient Asset Information
At step 7, the AI determines that the available asset information is insufficient to generate a reliable recommendation.
The system informs the Sustainability Officer that additional asset information is required.
The Sustainability Officer requests correction by an authorized Asset Custodian before requesting another recommendation.
E2 AI Service Unavailable
At step 6, the AI Recommendation Service is unavailable or fails to process the request.
The system displays an error message and allows the Sustainability Officer to retry the operation later.
E3 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.11.2 Review Sustainability Recommendations
Use Case ID: UC-18
Use Case Name: Review Sustainability Recommendations
Related Requirement: FR-13: Sustainability Recommendations
Detailed Requirements: FR-13.5 through FR-13.12; FR-13.19
Primary Actor: Sustainability Officer
Goal: Allow the Sustainability Officer to review AI-generated sustainability recommendations and their supporting explanations to evaluate the most appropriate action for a registered campus asset.
Preconditions: The Sustainability Officer is logged into the system and has permission to view sustainability recommendations. The asset is already registered in the system, and the AI Recommendation Service has successfully generated a sustainability recommendation for the selected asset.
Trigger: The Sustainability Officer selects a saved recommendation for review.
Postconditions: The Sustainability Officer has reviewed the AI-generated recommendation and its supporting explanation. The recommendation remains available for further decision-making, and no changes are made to the asset's status or information.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The Sustainability Officer navigates to the Sustainability Recommendations section.
2. The system displays a list of assets with available AI-generated recommendations.
3. The Sustainability Officer selects an asset from the list.
4. The system retrieves the sustainability recommendation associated with the selected asset.
5. The system displays the recommended action, such as reuse, transfer, repair, refurbishment, donation, recycling, or retirement.
6. The system displays explanatory asset information, available confidence or its absence, and cost and environmental estimates with units, sources, assumptions, and data limitations.
7. The Sustainability Officer reviews the recommendation and its supporting information.
8. The Sustainability Officer finishes reviewing the recommendation and may proceed to accept or reject it.
Alternative Flows
A1 No Recommendations Available
At step 2, the system finds no sustainability recommendations available for review.
The system displays a message indicating that no recommendations have been generated.
A2 Insufficient Supporting Information
At step 6, the Sustainability Officer determines that the recommendation lacks sufficient supporting information.
The Sustainability Officer may request a new recommendation after the relevant asset information has been updated.
Exception Flows
E1 Recommendation Not Found
At step 4, the system cannot retrieve the selected asset's recommendation.
The system displays an error message and allows the Sustainability Officer to return to the recommendations list.
E2 Unauthorized Access
The Sustainability Officer attempts to view a recommendation without the required permissions.
The system denies access and displays an appropriate error message.
7.11.3 Accept or Reject Sustainability Recommendations
Use Case ID: UC-19
Use Case Name: Accept or Reject Sustainability Recommendations
Related Requirement: FR-13: Sustainability Recommendations
Detailed Requirements: FR-13.13 through FR-13.17; FR-13.19 through FR-13.20
Primary Actor: Sustainability Officer
Goal: Allow the Sustainability Officer to accept or reject AI-generated sustainability recommendations after reviewing their explanations, ensuring that final decisions remain under human control.
Preconditions: The Sustainability Officer is logged into the system and has permission to review sustainability recommendations. The asset is already registered in the system, and an AI-generated sustainability recommendation is available for review.
Trigger: The Sustainability Officer selects Accept Recommendation or Reject Recommendation.
Postconditions: The Sustainability Officer's decision to accept or reject the recommendation is successfully recorded and stored in the system. If accepted, the recommendation is marked as accepted and forwarded for any required approvals before implementation. If rejected, the recommendation is marked as rejected, and the asset's current status remains unchanged. The Sustainability Officer receives a confirmation pop-up notification.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Sustainability Officer navigates to the Sustainability Recommendations section.
2. The system displays a list of assets with available AI-generated recommendations.
3. The Sustainability Officer selects an asset from the list.
4. The system displays the recommended sustainability action and its supporting explanation.
5. The Sustainability Officer reviews the recommendation and evaluates its suitability.
6. The Sustainability Officer clicks Accept Recommendation.
7. The system asks the Sustainability Officer to confirm the decision.
8. The Sustainability Officer confirms the acceptance.
9. The system rechecks that the recommendation is undecided and based on current relevant asset information, then records the acceptance, officer, and timestamp without changing the asset state.
10. The system forwards the accepted recommendation for any required approvals before the suggested action can be implemented.
11. The system displays a confirmation pop-up indicating that the decision has been recorded successfully.
Alternative Flows
A1 Recommendation Rejected
At step 6, the Sustainability Officer selects Reject Recommendation instead of accepting it.
The system asks the Sustainability Officer to provide a reason for rejection.
The Sustainability Officer enters the reason and confirms the rejection.
The system records the rejection, reason, officer, and timestamp and keeps the asset's current state unchanged.
A2 Decision Cancelled
At step 7, the Sustainability Officer cancels the confirmation.
The system returns to the recommendation details without recording a decision.
Exception Flows
E1 Recommendation No Longer Available
At step 4, the system determines that the selected recommendation is no longer available or has already been processed.
The system displays an error message and returns the Sustainability Officer to the recommendations list.
E2 Unauthorized Action
The Sustainability Officer attempts to accept or reject a recommendation without the required permissions.
The system denies the operation and displays an appropriate error message.
E3 Recommendation Outdated
At step 9 or before rejection is saved, relevant asset information has changed or another decision exists. The system blocks the decision, preserves the existing record, and asks the officer to review current information and request a new recommendation if needed.
E4 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.

7.13 Reporting

Example: Generate a monthly report of monitor transfers and retain exact totals when reviewing an AI summary.
7.13.1 Generate and Export Operational Report
Use Case ID: UC-39
Use Case Name: Generate and Export Operational Report
Related Requirement: FR-15 Reporting
Detailed Requirements: FR-15.1 through FR-15.8; FR-15.15 through FR-15.17
Primary Actor: Authorized User such as Asset Custodian, Department Representative, Procurement Officer or Finance Officer
Goal: Generate and Export Operational Report.
Preconditions: The user is authenticated and has report access for the selected records and fields.
Trigger: The user selects Operational Reports.
Postconditions: A scoped report is displayed, and a permitted CSV is produced if requested; source records remain unchanged.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user selects an operational report type, authorized department and date range.
2. The system validates the filters and rechecks report and field permissions.
3. The system retrieves eligible source records and computes conventional totals.
4. The system displays the report identifier, filters, generation timestamp, cutoff, totals and supporting records.
5. The user reviews the report and may select Export CSV.
6. The system rechecks current export permissions, generates only permitted columns and rows, and records the generation or export event.
Alternative Flows
A1 No Eligible Records
At step 3, no records match. The system displays an explicit no-data report rather than a retrieval error.
A2 Export Not Requested
At step 5, the user finishes viewing; no export is generated.
Exception Flows
E1 Invalid Filters
At step 2, the range or department is invalid. The system identifies the error and requests correction.
E2 Unauthorized Access or Export
At step 2 or 6, permission is absent or has changed. The system denies access or export without exposing restricted information.
E3 Generation or Export Failure
At step 3 or 6, retrieval, computation or file creation fails. The system reports the error, preserves source records and offers retry without claiming completion.
7.13.2 Generate Sustainability Report
Use Case ID: UC-40
Use Case Name: Generate Sustainability Report
Related Requirement: FR-15 Reporting
Detailed Requirements: FR-15.3 through FR-15.10; FR-15.15 through FR-15.17
Primary Actor: Sustainability Officer or Finance Officer with appropriate report permission
Goal: Generate Sustainability Report.
Preconditions: The user is authenticated and authorized for the selected sustainability and financial fields.
Trigger: The user selects Sustainability Reports.
Postconditions: A period-specific sustainability report is displayed with traceable calculations and explicit limitations, or missing-data indicators.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user selects the reporting period, category and authorized departmental scope.
2. The system validates permission and the reporting period and retrieves the required operational inputs.
3. The system calculates reuse and recorded financial indicators using the definitions in Section 6.3.
4. Where evidence exists, the system calculates waste diversion, asset life extension and carbon estimates using consistent units and documented boundaries.
5. The system displays metric definitions, source inputs, units, assumptions, data cutoff and missing-data indicators alongside the results.
6. The user reviews the report and may export its permitted values as CSV; the system records the report or export event.
Alternative Flows
A1 Insufficient Measurement Evidence
At step 3 or 4, a denominator is zero or required cost, mass, lifetime or emission data are missing. The affected result is marked unavailable; supported metrics remain visible.
A2 Sample Data
If test data are used, the report identifies them as illustrative and does not present them as measured university outcomes.
Exception Flows
E1 Invalid Period or Unauthorized Scope
At step 2, the system rejects the filters and requires correction or denies access.
E2 Calculation or Export Failure
The system reports the error, retains source records and does not display a failed calculation as a verified result.
7.13.3 Generate and Review AI Report Summary
Use Case ID: UC-41
Use Case Name: Generate and Review AI Report Summary
Related Requirement: FR-15 Reporting
Detailed Requirements: FR-15.11 through FR-15.17
Primary Actor: Authorized Report User
Supporting Actor: AI Report Summary Service
Goal: Generate and Review AI Report Summary.
Preconditions: The user is authenticated and authorized for an existing successfully generated report.
Trigger: The user selects Generate AI Summary for a report.
Postconditions: An AI draft and any accepted edits are associated with the source report; no underlying values or operational records are changed.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user selects a source report and requests an AI summary.
2. The system rechecks report permissions and sends only the permitted report content to the AI service.
3. The AI service returns a narrative draft based on the source report.
4. The system displays the draft label, source report reference, timestamp and relevant data limitations.
5. The user checks the narrative against the report, edits it if needed, and accepts it.
6. The system records the review decision and allows the accepted summary to be exported with its source report reference after a final permission check.
Alternative Flows
A1 Summary Rejected or Cancelled
At step 5, the user rejects or cancels the draft. The original report remains available and the rejected text is not exported as an accepted summary.
Exception Flows
E1 AI Service Unavailable
At step 3, generation fails. The system reports the error and offers the conventional report and CSV export.
E2 Unsupported Narrative or Incorrect Number
At step 5, the user identifies a claim not supported by the source report. The user corrects or rejects the draft; source totals are never altered to match the AI text.
E3 Unauthorized Access or Save Failure
The system denies unauthorized access or reports a failed decision/export save while preserving source records.
7.14 Authentication and Access Control

Example: A maintenance user can log in and view assigned repairs but cannot grant themselves finance access.
7.14.1 Log In
Use Case ID: UC-42
Use Case Name: Log In
Related Requirement: FR-1 Authentication and Access Control
Detailed Requirements: FR-1.1 through FR-1.5; FR-1.14; FR-1.17
Primary Actor: Campus User
Goal: Log In.
Preconditions: An account has been provisioned; the user has no valid authenticated session.
Trigger: The user submits the login form.
Postconditions: A session with assigned roles and department scope exists after successful authentication; failure creates no authorized session.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user opens the login screen and enters account credentials.
2. The system validates the credentials and confirms that the account is active.
3. The system establishes a protected session tied to the authenticated user and assigned roles.
4. The system records the login event and displays the functions permitted for that user.
Alternative Flows
A1 Existing Valid Session
When a valid session exists, the system may return the user to the permitted home screen without requesting credentials again.
Exception Flows
E1 Invalid Credentials or Inactive Account
At step 2, authentication fails. The system returns a generic error, records the failed attempt without credentials and grants no protected access.
E2 Authentication Service Failure
The system reports temporary unavailability and grants no authenticated session until validation succeeds.
7.14.2 Log Out or End Expired Session
Use Case ID: UC-43
Use Case Name: Log Out or End Expired Session
Related Requirement: FR-1 Authentication and Access Control
Detailed Requirements: FR-1.5 through FR-1.7; FR-1.14; FR-1.17
Primary Actor: Authenticated Campus User
Goal: Log Out or End Expired Session.
Preconditions: An authenticated session exists.
Trigger: The user selects Log Out, or the inactivity limit is reached.
Postconditions: The session is invalidated and all later protected requests require authentication.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user selects Log Out.
2. The system invalidates the authenticated session.
3. The system records the logout event and returns the user to the login screen.
4. A later protected request is denied until the user authenticates again.
Alternative Flows
A1 Inactivity Expiry
Instead of step 1, the session has 15 minutes of inactivity. The system expires it, records expiry and requires login before protected work resumes.
A2 Already Ended Session
If the session is already invalid, the system shows the login screen without restoring it.
Exception Flows
E1 Logout Request Cannot Reach Server
The interface reports the failure and does not falsely claim the server session has ended; inactivity expiry and server-side permission checks still apply.
7.14.3 Manage Accounts Roles and Departmental Access
Use Case ID: UC-44
Use Case Name: Manage Accounts Roles and Departmental Access
Related Requirement: FR-1 Authentication and Access Control
Detailed Requirements: FR-1.8 through FR-1.12; FR-1.14 through FR-1.17
Primary Actor: System Administrator
Goal: Manage Accounts Roles and Departmental Access.
Preconditions: The administrator has an active session with account-management authority.
Trigger: The administrator selects Create Account or Edit Account.
Postconditions: Validated account and permission changes and their audit entry are saved; removed access cannot be used in subsequent session operations.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The administrator selects an existing account or chooses Create Account.
2. The system displays permitted account, active-status, role and department-scope fields.
3. The administrator enters changes and confirms.
4. The system validates authority, mandatory fields, identifier uniqueness and supported scope, and checks that an active System Administrator will remain.
5. The system saves the account and audit change together and applies deactivation or permission reductions to active sessions.
6. The system displays confirmation.
Alternative Flows
A1 Change Cancelled
Before step 3, the administrator cancels. The account and permissions remain unchanged.
Exception Flows
E1 Invalid Account or Scope
At step 4, required details, uniqueness or permissions fail validation. The system identifies the error and prevents saving.
E2 Last Active Administrator
At step 4, the change would remove the last active administrator. The system blocks it.
E3 Unauthorized or Failed Save
The system denies an unauthorized operation or rolls back a failed save, preserving the prior account and permissions.
7.14.4 Review Security Audit Events
Use Case ID: UC-45
Use Case Name: Review Security Audit Events
Related Requirement: FR-1 Authentication and Access Control
Detailed Requirements: FR-1.13; FR-1.14; FR-1.17
Primary Actor: System Administrator
Goal: Review Security Audit Events.
Preconditions: The administrator is authenticated and authorized to view security logs.
Trigger: The administrator selects Security Audit Log.
Postconditions: Permitted events are displayed without changing recorded audit history.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The administrator selects a date range, user or event type.
2. The system validates filters and audit-view permission.
3. The system retrieves permitted matching security events.
4. The system displays event action, responsible identity where known, timestamp and nonsecret context.
5. The administrator reviews the events without editing or deleting their history.
Alternative Flows
A1 No Matching Events
At step 3, no events match; the system displays an empty result message.
Exception Flows
E1 Unauthorized or Invalid Filters
At step 2, the system denies access or requests valid filters.
E2 Retrieval Failure
At step 3, retrieval fails. The system reports the error and allows retry without modifying audit records.
7.15 LLM Powered Assistant

Example: Ask for two laboratory monitors, review the prepared request, then confirm submission without automatically reserving them.
7.15.1 Search for Assets Using Natural Language
Use Case ID: UC-46
Use Case Name: Search for Assets Using Natural Language
Related Requirement: FR-14 LLM Powered Assistant
Detailed Requirements: FR-14.1 through FR-14.4; FR-14.7; FR-14.12 through FR-14.15; FR-4.1 through FR-4.17
Primary Actor: Authenticated Authorized Campus User
Supporting Actor: LLM Assistant Service
Goal: Search for Assets Using Natural Language.
Preconditions: The user has an authenticated session with asset-search permission.
Trigger: The user asks the assistant to find an asset.
Postconditions: Authorized referenced search results are displayed; no quantity is reserved or asset changed.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user enters a natural-language resource need.
2. The assistant identifies the search intent and extracts the available criteria.
3. The system checks the user's scope and runs the existing asset search or matching function against current authorized listings.
4. The assistant returns referenced results and explains any uncertainty.
5. The user opens a permitted result or follows a link to the normal search screen.
Alternative Flows
A1 Ambiguous Need
At step 2, the asset, quantity or location is unclear. The assistant asks for clarification before searching.
A2 No Match
At step 3, no suitable listing is found. The assistant reports this and offers normal search or a later retry.
Exception Flows
E1 Unauthorized Information Requested
The system denies access to restricted results and does not include them in model context or output.
E2 Assistant Service Failure
The system displays an error and directs the user to ordinary search without changing any record.
7.15.2 Ask Record or Policy Questions
Use Case ID: UC-47
Use Case Name: Ask Record or Policy Questions
Related Requirement: FR-14 LLM Powered Assistant
Detailed Requirements: FR-14.1; FR-14.2; FR-14.4 through FR-14.7; FR-14.12 through FR-14.15
Primary Actor: Authenticated Authorized Campus User
Supporting Actor: LLM Assistant Service
Goal: Ask Record or Policy Questions.
Preconditions: The user has an authenticated session and may access the relevant records or approved policy material.
Trigger: The user asks an asset, request, transfer, policy or navigation question.
Postconditions: An answer identifies its supporting permitted records or policy sources; unsupported information is clearly identified and no records change.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The user asks a question and identifies a record if needed.
2. The system resolves the intended record or approved policy source and checks current access.
3. The assistant retrieves only permitted relevant information.
4. The assistant presents an answer with supporting record or policy references and data limitations.
5. The user may open a source record or the normal system screen.
Alternative Flows
A1 Clarification Needed
At step 2, several records could match. The assistant asks the user to identify the intended record.
A2 No Supporting Evidence
At step 3, the required record or approved policy text is unavailable. The assistant states that it cannot determine the answer and offers normal navigation.
Exception Flows
E1 Access Denied or Unsafe Instruction
The system denies unauthorized retrieval and treats instructions in retrieved material as data, not authority to bypass controls.
E2 LLM or Retrieval Failure
The system reports the failure and retains direct access to permitted normal record screens.
7.15.3 Prepare and Confirm a Resource Request Through the Assistant
Use Case ID: UC-48
Use Case Name: Prepare and Confirm a Resource Request Through the Assistant
Related Requirement: FR-14 LLM Powered Assistant
Detailed Requirements: FR-14.1; FR-14.2; FR-14.4; FR-14.8 through FR-14.16; FR-5.1 through FR-5.9; FR-5.16 through FR-5.20
Primary Actor: Department Representative
Supporting Actor: LLM Assistant Service
Goal: Prepare and Confirm a Resource Request Through the Assistant.
Preconditions: The representative is authenticated and authorized to submit requests for the selected department.
Trigger: The representative asks the assistant to prepare a resource request.
Postconditions: Only an explicitly confirmed and validated request is saved as Pending Approval with a request identifier; no reservation or approval occurs.
Failure Postconditions: Failure does not grant unauthorized access or commit partial business changes. Previously saved records remain intact.
Main Success Scenario
1. The representative describes the departmental need.
2. The assistant gathers category, purpose, specifications, quantity, preferred condition, urgency, destination and required date, and any selected asset.
3. The system displays the full proposed request and represented department for review.
4. The representative corrects details if needed and explicitly confirms submission.
5. The system rechecks current authority, required fields, date and asset information and submits once through the normal resource-request workflow.
6. The system returns the request identifier and Pending Approval status and records the confirmed operation without creating a reservation.
Alternative Flows
A1 Draft Corrected
At step 4, the user edits the draft and reviews the revised values before confirmation.
A2 Draft Cancelled
Before confirmation, the user cancels; no request is saved.
Exception Flows
E1 Missing Details or Changed Availability
At step 5, validation fails. The system identifies the problem and requests correction and renewed confirmation.
E2 Unauthorized or AI Service Failure
The system denies unauthorized submission, or directs the user to the ordinary request form if assistant processing fails.
E3 Repeated Confirmation or Save Failure
A repeated confirmation cannot create a duplicate request. A failed submission preserves existing records and reports that no new request has been confirmed.

