Section 6: Other Requirements
This section defines the system states and sustainability measurement requirements of the Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System. These requirements establish the operational restrictions, approval responsibilities, and methods used to evaluate the system's effectiveness in improving resource utilization, reducing unnecessary purchases, and promoting sustainability.
6.1 Business Rule References
Operational business rules are specified in Section 5.5. The following subsections define state constraints, measurement methods and additional data requirements.
6.2 System States
The system shall maintain clearly defined states for assets, resource requests, reservations, transfers, and maintenance activities. These states will allow authorized users to monitor progress and ensure that operations follow the appropriate workflows.
6.2.1 Asset States
Registered: The asset has been recorded in the system.
Available: The asset is available for reuse or reservation.
Reserved: The asset has been allocated to an approved reservation.
Under Maintenance: The asset is undergoing inspection, maintenance, or repair.
Transferred: The asset has been successfully transferred to another department.
Donated: The asset has been donated following the required approval.
Recycled: The asset has been processed for recycling.
Retired: The asset has been removed from active university use.
Disposed: The asset has been permanently removed through an approved disposal process.
6.2.2 Resource Request States
Pending Approval: The request has been submitted and is awaiting a decision.
Approved: The request has been approved by an authorized user.
Rejected: The request has been rejected by an authorized user.
Fulfilled: The requested resource has been successfully received.
Cancelled: The request has been cancelled before completion.
6.2.3 Reservation States
Active: The reservation has been approved and the asset quantity has been reserved.
Cancelled: The reservation has been cancelled and the reserved quantity has been released.
Fulfilled: The reserved asset has been successfully transferred and received.
6.2.4 Transfer States
Awaiting Dispatch: The transfer has been approved but the asset has not yet been dispatched.
In Transit: The asset has been dispatched and is awaiting receipt confirmation.
Completed: The receiving department has confirmed receipt, and the asset's location and custody have been updated.
6.2.5 Maintenance States
Defect Reported: A defect has been reported for the asset.
Inspection Requested: An inspection request has been submitted.
In Progress: The asset is currently undergoing maintenance or repair.
Repair Completed: The repair has been completed and recorded.
Further Repair Required: The previous repair attempt was unsuccessful or additional maintenance is necessary.
6.2.6 State Transition Rules
Publication status is separate from life-cycle state. Registered assets become Available only when an authorized custodian confirms that their condition permits reuse. Available quantities become Reserved only through request approval; cancellation before dispatch restores their availability once.
For quantity-based lots, available and reserved quantities are tracked separately rather than assigning one misleading status to every unit. Total allocated units cannot exceed eligible stock. Transfer completion moves only the received reserved units to the destination; transferred units remain in history and require an authorized receiving-custodian release before being offered again.
Requests follow Pending Approval to Approved, Rejected or Cancelled. Approved requests become Fulfilled through receipt confirmation, or Cancelled through eligible reservation cancellation. A terminal request cannot be edited or decided again.
Reservations follow Active to Cancelled before dispatch, or Active to Fulfilled through receipt confirmation. Transfers follow Awaiting Dispatch to In Transit to Completed; a failed delivery or unresolved discrepancy remains In Transit. No generic form may skip receipt confirmation.
Maintenance can move from Defect Reported or Inspection Requested to In Progress, then Repair Completed or Further Repair Required. Further Repair Required can return to In Progress. A condition assessment and an authorized asset-state update are required before reuse; repair completion alone does not restore availability.
Available or otherwise eligible units may enter Under Maintenance or an approved end-of-life workflow only after conflicting commitments are resolved. Donation, recycling, retirement and disposal require an independent approval reference and completion event. Disposed or recycled units cannot return to available stock through a generic edit.
6.2.7 End of Life Proposal States
An end-of-life proposal is Pending Review until an independently authorized Approver records Approved or Rejected. Approval permits the matching action workflow but does not itself change asset state. A completed physical action is recorded separately with the approved reference in the asset history.
6.3 Sustainability and Financial Performance Measurement
The system shall evaluate its effectiveness using measurable indicators related to financial savings, asset reuse, waste reduction, and resource life-cycle extension. These indicators will help the university assess whether the platform reduces unnecessary purchases and improves the utilization of existing resources.
6.3.1 Financial Savings and Avoided Purchases
One of the primary measures of success will be the reduction in unnecessary asset purchases after implementing the Circular Campus system.
The university's spending on selected asset categories, such as computers, monitors, furniture, and laboratory equipment, will be compared across equivalent periods before and after implementation.
Financial Savings = Baseline Asset Spending − Post-Implementation Asset Spending
The comparison shall use equivalent time periods and account for significant changes in asset demand, prices, and departmental activity.
Additionally, the system shall estimate avoided purchase costs by identifying assets that were reused instead of purchasing equivalent new resources.
Estimated Avoided Purchase Savings = Equivalent New Asset Cost minus Reuse Preparation, Repair, Refurbishment and Transfer Costs
These estimates shall be reported separately from observed changes in total spending to avoid incorrectly attributing all spending reductions to the system.
6.3.2 Asset Reuse Rate
The system shall measure the percentage of eligible available assets that were successfully reused or transferred to other departments.
Asset Reuse Rate (%) = (Number of Assets Successfully Reused ÷ Total Eligible Available Assets) × 100
A higher reuse rate indicates improved utilization of existing campus resources.
6.3.3 Asset Life Extension
The system shall measure how maintenance, repair, refurbishment, and reuse contribute to extending the useful life of campus assets.
Asset Life Extension = Actual or Estimated Useful Life After Intervention − Expected Useful Life Without Intervention
These values shall be based on available maintenance records, asset condition, and documented assumptions.
6.3.4 Waste Diversion
Waste diverted is the documented mass of eligible units kept out of final disposal through reuse, repair, refurbishment, donation or verified recycling within the reporting period. Count each physical unit once for this measure and identify which recovery routes are included. Waste Diversion Rate percent = Diverted Mass divided by Total Eligible Waste Mass multiplied by 100. Use the same category, period and mass units in numerator and denominator; a zero or missing denominator produces unavailable, not zero. Estimated masses must be labelled with their source and assumptions.
6.3.5 Estimated Carbon Emission Reduction
Estimated Carbon Reduction in kg CO2e = Comparable New Asset Scenario Emissions minus Reuse Scenario Emissions. The reuse scenario includes recorded or estimated repair, refurbishment and transport emissions within the stated boundary. Use comparable function, quantities, time period and emission-factor boundaries, document the factor source and date, and show an increase as a negative benefit rather than hiding it. If a defensible baseline or factor is missing, show unavailable; do not invent an emission factor.
6.3.6 Counting and Evidence Rules
For reuse rate, use the same cohort of physical units that were eligible and available during the reporting period in both numerator and denominator, and count each reused unit at most once. For quantity-based asset records, count units consistently rather than mixing records and units. Avoided purchases require a documented departmental need fulfilled by reused units; include applicable repair, refurbishment and transfer costs. Keep observed spending changes, estimated avoided costs and AI narratives separate. Useful-life extension is an estimate requiring a documented comparison and must not be presented as measured causal proof.
6.4 Success Evaluation Criteria
The effectiveness of the Circular Campus system shall be evaluated by comparing relevant operational, financial, and sustainability indicators before and after implementation.
SC-1: Reduced Asset Spending
The system's financial impact shall be assessed by comparing spending on selected asset categories across equivalent periods before and after implementation, accounting for differences in prices and demand.
SC-2: Increased Asset Reuse
The system shall track the number and percentage of eligible campus assets successfully reused or transferred between departments.
SC-3: Reduced Unnecessary Purchases
The system shall record instances where existing campus assets fulfilled departmental needs that would otherwise have required purchasing new resources.
SC-4: Improved Resource Allocation
The system shall measure the percentage of approved resource requests successfully fulfilled using existing campus assets.
SC-5: Improved Maintenance and Asset Life Extension
The system shall track completed repairs, refurbished assets, and estimated extensions to asset useful life.
SC-6: User Acceptance
The system shall collect feedback from authorized users to evaluate the usefulness of asset searching, resource requests, AI recommendations, and overall system usability.
SC-7: AI Recommendation Usefulness
The system shall measure the percentage of AI-generated classification, matching, and sustainability recommendations accepted or modified by authorized users.
6.5 Measurement Limitations and Assumptions
The accuracy of the system's financial and sustainability measurements will depend on the availability and quality of university asset records, purchasing information, maintenance costs, and environmental data.
Financial savings estimates shall distinguish between actual spending reductions and estimated avoided purchases. Similarly, environmental benefits shall be presented as estimates when direct measurements are unavailable.
Because the project is being developed as a university prototype, access to historical procurement records and long-term operational data may be limited. Where actual before-and-after comparisons cannot be performed, the team may demonstrate the proposed measurement methods using clearly labeled sample or simulated data.
The system shall clearly communicate these limitations to prevent misleading conclusions about its financial and environmental impact.
6.6 Database Requirements
The system shall assign a unique identifier to every registered asset and maintain accurate records of asset ownership, condition, location, and availability. It shall preserve historical records of requests, approvals, transfers, maintenance, and disposal activities to ensure data integrity and traceability. Database access shall be restricted according to user roles, and appropriate backup and recovery procedures shall be implemented to prevent data loss.
6.7 Legal and Regulatory Considerations
The system shall be designed to protect personal information in accordance with applicable UAE data protection legislation, including Federal Decree-Law No. 45 of 2021 concerning the Protection of Personal Data, where applicable. The system shall also follow relevant Khalifa University policies regarding information security, asset management, and authorized access.
Asset recycling and disposal processes shall take into consideration applicable UAE environmental and waste management regulations. The system shall maintain records of disposal approvals and actions to support accountability and compliance with relevant university procedures.
6.8 Asset Reuse and Disposal Requirements
The system shall prioritize identifying opportunities for asset reuse, repair, refurbishment, or transfer before recommending recycling or disposal. Assets shall not be permanently disposed of without the required authorization, and relevant life-cycle events shall be recorded. The system shall support sustainability reporting by tracking reused assets, avoided purchases, estimated financial savings, and waste reduction.



Section 7 Detailed Use Case Descriptions
This section describes how authorized users carry out each system feature. Every use case identifies its requirement links, actors, trigger, preconditions, outcomes, normal steps, alternatives, and exceptions. Requirement identifiers are retained from Section 4; use-case identifiers are stable even when their section numbers differ.
A precondition describes the normal starting situation. Permissions, current status, and availability are rechecked before protected data is shown or a change is saved so that concurrent changes cannot bypass the rules.
 
7.1 Asset Registration
Rules: Registration and ordinary edits require custodian authority. Quantity is a positive whole number and value is nonnegative. Generic edits cannot bypass approval or transfer controls. A saved record remains valid if its confirmation email fails.

Example: Register a laboratory monitor, view its record, or correct its description.
7.1.1 Register Asset
Use Case ID: UC-01
Use Case Name: Register Asset
Related Requirement: FR-2: Asset Registration
Detailed Requirements: FR-2.1 through FR-2.4; FR-2.9 through FR-2.16; FR-2.17
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to register a new campus asset in the system.
Preconditions: The Asset Custodian is logged in and has permission to register assets.
Trigger: The Asset Custodian selects the Register Asset option.
Postconditions: The new asset is successfully registered, and its information is stored in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been registered successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian selects the Register Asset option.
2. The system displays the asset registration form.
3. The Asset Custodian enters the asset name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability.
4. The Asset Custodian submits the registration form.
5. The system rechecks registration permission and validates mandatory fields, positive whole-number quantity, and nonnegative estimated value.
6. The system assigns a unique asset identifier and saves the asset with its initial registration history entry.
7. The system displays a confirmation pop-up indicating successful asset registration.
8. The system sends a confirmation email to the Asset Custodian's registered email address.
Alternative Flows
A1 Registration Cancelled
Before submitting, the Asset Custodian cancels the registration.
The system returns to the previous page without saving the asset.
Exception Flows
E1 Missing or Invalid Information
At step 5, the system detects missing or invalid information.
The system displays an error message identifying the issue.
The Asset Custodian corrects the information and resubmits the form.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E4 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.1.2 View Registered Asset
Use Case ID: UC-02
Use Case Name: View Registered Asset
Related Requirement: FR-2: Asset Registration
Detailed Requirements: FR-2.5; FR-2.6; FR-2.9; FR-2.17
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to view the details of an asset registered in the system.
Preconditions: The Asset Custodian is logged in, has permission to view the asset, and the asset is already registered in the system.
Trigger: The Asset Custodian opens Asset Management within the authenticated session.
Postconditions: The system displays the selected asset's information without modifying its stored data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The Asset Custodian opens Asset Management within the authenticated session.
2. The Asset Custodian navigates to the Asset Management section.
3. The system displays a list of registered assets that the custodian is authorized to access.
4. The Asset Custodian selects an asset from the list.
5. The system retrieves the selected asset's information.
6. The system displays the asset's name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability.
Alternative Flows
A1 No Registered Assets
At step 3, the system finds no registered assets accessible to the Asset Custodian.
The system displays a message indicating that no assets are available.
Exception Flows
E1 Asset Not Found
At step 5, the selected asset no longer exists or cannot be retrieved.
The system displays an error message and allows the Asset Custodian to return to the asset list.
E2 Unauthorized Access
At step 5, the Asset Custodian does not have permission to view the selected asset.
The system denies access and displays an appropriate error message.
7.1.3 Update Asset Information
Use Case ID: UC-03
Use Case Name: Update Asset Information
Related Requirement: FR-2: Asset Registration
Detailed Requirements: FR-2.7 through FR-2.14; FR-2.16; FR-2.17
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to update the information of an existing registered asset to ensure that its details remain accurate and up to date.
Preconditions: The Asset Custodian is logged in, has permission to modify the selected asset, and the asset is already registered in the system.
Trigger: The Asset Custodian navigates to the Asset Management section.
Postconditions: The updated asset information is successfully saved in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset information has been updated successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays a list of registered assets.
3. The Asset Custodian selects an asset and clicks Edit Asset.
4. The system displays the asset's current information.
5. The Asset Custodian modifies the required fields.
6. The Asset Custodian submits the updated information.
7. The system rechecks authority and validates the changes, rejects edits that bypass controlled workflows, and saves the updated record with the responsible user and timestamp.
8. The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1 Update Cancelled
The Asset Custodian cancels the update, and the system keeps the original asset information unchanged.
Exception Flows
E1 Invalid Information
The system displays an error message and asks the Asset Custodian to correct the information.
E2 Unauthorized Update
The system denies the update if the Asset Custodian does not have the required permissions.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E4 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.2 Asset Publication
Rules: Publication changes visibility; it does not approve allocation. Eligible asset state is rechecked before publication. Unpublication is blocked by active reservations or pending transfers.

Example: Publish an idle monitor for other departments, then unpublish it only when no active commitment prevents removal.
7.2.1 Publish Asset
Use Case ID: UC-04
Use Case Name: Publish Asset
Related Requirement: FR-3: Asset Publication
Detailed Requirements: FR-3.1 through FR-3.5; FR-3.12 through FR-3.19
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to publish surplus, idle, or unwanted campus assets so that other authorized users and departments can view and request them.
Preconditions: The Asset Custodian is logged in, has permission to publish assets, and the asset is already registered in the system.
Trigger: The Asset Custodian navigates to the Asset Management section.
Postconditions: The selected asset is successfully published and becomes visible to other authorized users and departments. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been published successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays the registered assets.
3. The Asset Custodian selects an asset to publish.
4. The Asset Custodian clicks Publish Asset.
5. The system displays the asset details and asks for confirmation.
6. The Asset Custodian confirms publication.
7. The system rechecks authority, current publication state, and eligibility for sharing, then saves publication status Published.
8. The asset becomes visible to other authorized users.
9. The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1 Asset Already Published
The system informs the Asset Custodian that the asset is already published.
A2 Publication Cancelled
The Asset Custodian cancels the process, and the asset remains unpublished.
Exception Flows
E1 Unauthorized Publication
The system denies publication if the user does not have the required permissions.
E2 Asset State Ineligible
Before the publication is saved at step 7, the asset state does not permit sharing. The system blocks publication and explains the restriction.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E4 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.2.2 Unpublish Asset
Use Case ID: UC-05
Use Case Name: Unpublish Asset
Related Requirement: FR-3: Asset Publication
Detailed Requirements: FR-3.6 through FR-3.9; FR-3.12; FR-3.14 through FR-3.19
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to remove a previously published asset from public listings when it is no longer available for sharing or transfer.
Preconditions: The Asset Custodian is logged in, has permission to manage the selected asset, and the asset is already published in the system.
Trigger: The Asset Custodian navigates to the Asset Management section.
Postconditions: The selected asset is successfully unpublished and is no longer visible in the available asset listings to other departments. The asset's information remains stored in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been unpublished successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian navigates to the Asset Management section.
2. The system displays the registered assets.
3. The Asset Custodian selects a published asset.
4. The Asset Custodian clicks Unpublish Asset.
5. The system displays a confirmation message.
6. The Asset Custodian confirms the action.
7. The system rechecks authority, publication state, and active reservations or pending transfers immediately before saving.
8. If no restrictions exist, the system changes the asset's publication status to Unpublished.
9. The asset is removed from the available asset listings.
10. The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1 Asset Already Unpublished
The system informs the Asset Custodian that the selected asset is not currently published.
A2 Active Reservations or Pending Transfers
The system prevents unpublishing the asset and informs the Asset Custodian that existing requests or transfers must be resolved first.
A3 Unpublishing Cancelled
The Asset Custodian cancels the operation, and the asset remains published.
Exception Flows
E1 Unauthorized Action
The system denies the operation if the Asset Custodian lacks the required permissions.
E2 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E3 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.2.3 View Published Assets
Use Case ID: UC-06
Use Case Name: View Published Assets
Related Requirement: FR-3: Asset Publication
Detailed Requirements: FR-3.5; FR-3.10 through FR-3.12
Primary Actor: Authorized User (Department Representative or Asset Custodian)
Goal: Allow authorized users to view assets published by different university departments to identify resources available for reuse or transfer.
Preconditions: The user is authenticated and permitted to view published assets; the catalogue may be empty.
Trigger: The user opens Available Assets within the authenticated session.
Postconditions: The system displays the published assets and their relevant information without modifying any stored asset data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user opens Available Assets within the authenticated session.
2. The user navigates to the Available Assets section.
3. The system retrieves all published assets that the user is authorized to view.
4. The system displays a list of published assets.
5. The user selects an asset from the list.
6. The system displays the asset's name, description, category, quantity, department, location, condition, estimated value, and availability.
7. The user reviews the asset information.
Alternative Flows
A1 No Published Assets
At step 3, the system finds no published assets.
The system displays a message indicating that no assets are currently available.
A2 Asset No Longer Available
At step 5, the selected asset has been unpublished or is no longer available.
The system informs the user that the asset is unavailable and returns to the asset listings.
Exception Flows
E1 Unauthorized Access
The user attempts to view an asset they do not have permission to access.
The system denies access and displays an appropriate error message.
E2 Retrieval Failure
When the system retrieves the selected information, the operation fails. The system reports the failure and allows a return to the list or a retry without changing any stored record.
7.3 AI Assisted Asset Classification
Rules: AI outputs are advisory. Display the explanation and available confidence. Use the AI service's supplied confidence scale and low-confidence threshold when both are available. Otherwise identify the confidence assessment as unavailable and require manual review. Accepted classification is applied only to the registration form; registration saves the asset record.

Example: Generate a suggested category for a monitor, inspect its explanation, and confirm the accepted classification.
7.3.1 Generate AI Asset Classification
Use Case ID: UC-07
Use Case Name: Generate AI Asset Classification
Related Requirement: FR-11: AI-Assisted Asset Classification
Detailed Requirements: FR-11.1 through FR-11.10; FR-11.14 through FR-11.16; FR-11.19 through FR-11.23; FR-11.24
Primary Actor: Asset Custodian
Supporting Actor: AI Classification Service
Goal: Allow the Asset Custodian to use AI to automatically generate recommended categories, tags, and standardized descriptions for newly registered campus assets, reducing manual effort and improving classification accuracy.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The Asset Custodian has entered the necessary asset information, such as the asset name, description, and specifications.
Trigger: The Asset Custodian navigates to the Register Asset section.
Postconditions: The AI generates recommended categories, tags, and a standardized description for the asset. The recommendations are displayed to the Asset Custodian for review and are not applied until the Asset Custodian accepts them.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The Asset Custodian navigates to the Register Asset section.
2. The Asset Custodian enters the asset's name, description, and relevant specifications.
3. The Asset Custodian clicks Generate AI Classification.
4. The system sends the entered asset information to the AI Classification Service.
5. The AI analyzes the provided information and generates a recommended category, tags, and standardized description.
6. The system displays the recommended classification with an explanation, any confidence supplied by the AI service, and a low-confidence warning when applicable.
7. The Asset Custodian reviews the recommendations.
8. The Asset Custodian accepts the recommendations.
9. The system fills the relevant registration fields with the accepted recommendations.
10. The Asset Custodian can continue with the asset registration process.
Alternative Flows
A1 Recommendations Rejected
At step 7, the Asset Custodian rejects the AI-generated recommendations.
The system allows the Asset Custodian to manually enter the category, tags, and description.
A2 Recommendations Modified
At step 7, the Asset Custodian partially agrees with the recommendations.
The system allows the Asset Custodian to edit the suggested information before applying it.
Exception Flows
E1 Insufficient Asset Information
At step 5, the AI cannot generate suitable recommendations because the provided information is insufficient.
The system asks the Asset Custodian to provide additional asset details.
E2 AI Service Unavailable
At step 4, the AI Classification Service is unavailable.
The system displays an error message and allows the Asset Custodian to classify the asset manually.
E3 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.3.2 Review and Modify AI Classification Recommendations
Use Case ID: UC-08
Use Case Name: Review and Modify AI Classification Recommendations
Related Requirement: FR-11: AI-Assisted Asset Classification
Detailed Requirements: FR-11.5 through FR-11.10; FR-11.17 through FR-11.23; FR-11.24
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to review, accept, reject, or modify AI-generated asset classification recommendations to ensure that the asset information is accurate and appropriate.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The AI Classification Service has successfully generated classification recommendations for the asset.
Trigger: The Asset Custodian selects the recommendations they want to modify.
Postconditions: The Asset Custodian's accepted or modified classification information is applied to the asset registration form. If the recommendations are rejected, the Asset Custodian can manually enter the classification information. No changes are saved to the asset record until registration is submitted.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The AI Classification Service generates recommended categories, tags, and a standardized description.
2. The system displays the recommendations, explanatory factors, confidence when available, and any uncertainty warning.
3. The Asset Custodian reviews the suggested classification information.
4. The Asset Custodian selects the recommendations they want to modify.
5. The system allows the Asset Custodian to edit the category, tags, or description.
6. The Asset Custodian confirms the modified recommendations; the system validates them and rechecks the user's permission to apply them.
7. The system applies the confirmed information to the asset registration form.
8. The system displays a confirmation message.
Alternative Flows
A1 Recommendations Accepted Without Changes
At step 4, the Asset Custodian accepts all AI recommendations.
The system applies the recommendations without modification.
A2 Recommendations Rejected
At step 4, the Asset Custodian rejects the recommendations.
The system allows manual classification of the asset.
A3 Review Cancelled
The Asset Custodian cancels the review.
The system returns to the registration form without applying the recommendations.
Exception Flows
E1 Invalid Modified Information
At step 6, the system detects invalid or missing required information.
The system displays an error message and asks the Asset Custodian to correct it.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.3.3 Regenerate AI Classification Recommendations
Use Case ID: UC-09
Use Case Name: Regenerate AI Classification Recommendations
Related Requirement: FR-11: AI-Assisted Asset Classification
Detailed Requirements: FR-11.11 through FR-11.23; FR-11.24
Primary Actor: Asset Custodian
Supporting Actor: AI Classification Service
Goal: Allow the Asset Custodian to request new AI-generated classification recommendations when the initial suggestions are inaccurate, incomplete, or unsuitable for the asset.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The AI Classification Service has already generated initial recommendations for the asset.
Trigger: The Asset Custodian clicks Regenerate Recommendations.
Postconditions: The AI generates and displays a new set of classification recommendations based on the available or updated asset information. The Asset Custodian can review, accept, or modify the new recommendations before applying them to the registration form.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The Asset Custodian reviews the initial AI-generated classification recommendations.
2. The Asset Custodian determines that the recommendations are unsuitable.
3. The Asset Custodian modifies or adds asset information to improve the results.
4. The Asset Custodian clicks Regenerate Recommendations.
5. The system sends the updated asset information to the AI Classification Service.
6. The AI analyzes the information and generates new recommended categories, tags, and a standardized description.
7. The system displays new recommendations with explanations and available confidence, retaining previously accepted form information until the user confirms replacement.
8. The Asset Custodian reviews the updated recommendations.
9. The Asset Custodian accepts the recommendations.
10. The system applies the accepted information to the asset registration form.
Alternative Flows
A1 Recommendations Rejected
At step 8, the Asset Custodian rejects the new recommendations.
The system allows the Asset Custodian to regenerate recommendations again or manually classify the asset.
A2 Regeneration Cancelled
The Asset Custodian cancels the regeneration process.
The system retains the previously displayed recommendations without applying changes.
Exception Flows
E1 AI Service Unavailable
At step 5, the AI Classification Service is unavailable.
The system displays an error message and allows the Asset Custodian to classify the asset manually.
E2 Insufficient Asset Information
At step 6, the AI cannot generate suitable recommendations.
The system asks the Asset Custodian to provide additional asset information.
E3 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.4 Asset Search and Filtering
Rules: Search uses case-insensitive text matching; filters combine using AND. Restricted listings are excluded. Missing filter data cannot satisfy a corresponding numeric constraint. Results do not allocate stock.

Example: Search for monitors and filter by location and at least two available units before opening a result.
7.4.1 Search Available Assets
Use Case ID: UC-20
Use Case Name: Search Available Assets
Related Requirement: FR-4: Asset Search and Filtering
Detailed Requirements: FR-4.1 through FR-4.4; FR-4.9; FR-4.10; FR-4.14 through FR-4.16
Primary Actor: Authorized User (Department Representative or Asset Custodian)
Goal: Allow authorized users to search for available campus assets to identify resources suitable for reuse or transfer.
Preconditions: The user is logged into the system and has permission to view published assets.
Trigger: The user navigates to the Available Assets section.
Postconditions: The system displays the available assets matching the user's search criteria without modifying any stored asset data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user navigates to the Available Assets section.
2. The system displays the asset search option.
3. The user enters an asset name, keyword, or description.
4. The user submits the search.
5. The system performs case-insensitive text matching against names and descriptions of published assets the user is authorized to view.
6. The system displays the available assets matching the search criteria.
7. The user reviews the search results.
Alternative Flows
A1 No Matching Assets
At step 5, the system finds no available assets matching the search criteria.
The system displays a message indicating that no matching assets are available.
The user modifies the search criteria and submits the search again.
A2 Empty Search
At step 4, the user submits the search without entering a keyword.
The system displays all available published assets that the user is authorized to view.
Exception Flows
E1 Search Failed
At step 5, the system cannot retrieve the asset information.
The system displays an error message and allows the user to try again.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.4.2 Filter Available Assets
Use Case ID: UC-21
Use Case Name: Filter Available Assets
Related Requirement: FR-4: Asset Search and Filtering
Detailed Requirements: FR-4.5 through FR-4.10; FR-4.14 through FR-4.17
Primary Actor: Authorized User (Department Representative or Asset Custodian)
Goal: Allow authorized users to filter available campus assets based on category, condition, location, quantity, availability, age, and estimated value.
Preconditions: The user is logged into the system and has permission to view published assets.
Trigger: The user navigates to the Available Assets section.
Postconditions: The system displays the available assets matching the selected filters without modifying any stored asset data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user navigates to the Available Assets section.
2. The system displays the available assets and filtering options.
3. The user selects one or more category, condition, department, location, available-quantity, availability, age, estimated-value, or life-cycle-state filters.
4. The user clicks Apply Filters.
5. The system validates numeric values and ranges and excludes assets missing a value required by the selected filter.
6. The system retrieves the available assets matching the selected filters and any entered search criteria.
7. The system displays the filtered asset list.
8. The user reviews the filtered results.
Alternative Flows
A1 No Matching Assets
At step 6, the system finds no available assets matching the selected filters.
The system displays a message indicating that no matching assets are available.
The user modifies or removes the filters.
A2 Filters Cleared
The user clicks Clear Filters.
The system removes the selected filters and displays the assets matching any remaining search criteria.
Exception Flows
E1 Invalid Filter Values
At step 5, the system detects invalid filter values, such as a minimum estimated value greater than the maximum estimated value.
The system displays an error message identifying the issue.
The user corrects the filter values and applies the filters again.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
E3 Retrieval Failure
When the system retrieves the selected information, the operation fails. The system reports the failure and allows a return to the list or a retry without changing any stored record.
7.4.3 View Asset Search Result Details
Use Case ID: UC-22
Use Case Name: View Asset Search Result Details
Related Requirement: FR-4: Asset Search and Filtering
Detailed Requirements: FR-4.9; FR-4.11 through FR-4.16
Primary Actor: Authorized User (Department Representative or Asset Custodian)
Goal: Allow authorized users to view the details of an asset displayed in the search or filtered results to assess whether it meets their needs.
Preconditions: The user is logged into the system, has permission to view the selected asset, and the asset appears in the search or filtered results.
Trigger: The user selects an asset from the results.
Postconditions: The system displays the selected asset's information without modifying its stored data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The system displays the asset search or filtered results.
2. The user selects an asset from the results.
3. The system checks the user's permission to view the selected asset.
4. The system retrieves the selected asset's current information.
5. The system displays current name, description, specifications, category, quantity, department, location, condition, purchase date, age, estimated value, availability, life-cycle state, and accessible supporting information.
6. The user reviews the asset information.
Alternative Flows
A1 Asset No Longer Available
At step 4, the selected asset has been unpublished or is no longer available.
The system informs the user that the asset is unavailable and returns to the search results.
Exception Flows
E1 Asset Not Found
At step 4, the selected asset no longer exists or cannot be retrieved.
The system displays an error message and allows the user to return to the search results.
E2 Unauthorized Access
At step 3, the user does not have permission to view the selected asset.
The system denies access and displays an appropriate error message.
7.5 Resource Requests
Rules: New requests start Pending Approval. Requests without a selected asset may remain pending but cannot be approved. Only Pending Approval requests without active reservations or transfers can be edited. A saved request remains valid if its confirmation email fails.

Example: Request two monitors for a teaching laboratory and correct the required date before approval.
7.5.1 Submit Resource Request
Use Case ID: UC-23
Use Case Name: Submit Resource Request
Related Requirement: FR-5: Resource Requests
Detailed Requirements: FR-5.1 through FR-5.9; FR-5.16 through FR-5.20
Primary Actor: Department Representative
Goal: Allow the Department Representative to submit a request for resources required by their department.
Preconditions: The Department Representative is logged into the system and has permission to submit resource requests on behalf of their department.
Trigger: The Department Representative selects the Submit Resource Request option.
Postconditions: The new resource request is successfully submitted, and its information is stored in the system. The Department Representative receives a confirmation pop-up notification and an email confirming that the resource request has been submitted successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Department Representative selects the Submit Resource Request option.
2. The system displays the resource request form.
3. The Department Representative enters category, purpose, specifications, quantity, preferred condition or Any, urgency, destination, and required date, and may select an accessible published asset.
4. The Department Representative submits the request form.
5. The system validates required fields, positive whole-number quantity, required date, departmental authority, and the selected asset reference if supplied.
6. The system assigns a unique request identifier, links the requesting user and department, and saves the request as Pending Approval with a submission timestamp; no quantity is reserved.
7. The system displays a confirmation pop-up indicating successful request submission.
8. The system sends a confirmation email to the Department Representative's registered email address.
Alternative Flows
A1 Request Submission Cancelled
Before submitting, the Department Representative cancels the request.
The system returns to the previous page without saving the request.
Exception Flows
E1 Missing or Invalid Information
At step 5, the system detects missing or invalid information.
The system displays an error message identifying the issue.
The Department Representative corrects the information and resubmits the form.
E2 Unauthorized Submission
The Department Representative attempts to submit a request for a department they are not authorized to represent.
The system denies submission and displays an appropriate error message.
E3 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E4 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.5.2 View Resource Request
Use Case ID: UC-24
Use Case Name: View Resource Request
Related Requirement: FR-5: Resource Requests
Detailed Requirements: FR-5.10; FR-5.11; FR-5.18
Primary Actor: Department Representative
Goal: Allow the Department Representative to view the details of a resource request submitted by their department.
Preconditions: The Department Representative is logged in, has permission to view the request, and the request is already stored in the system.
Trigger: The Department Representative navigates to the Resource Requests section.
Postconditions: The system displays the selected resource request's information without modifying its stored data.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The Department Representative navigates to the Resource Requests section.
2. The system displays the resource requests that the Department Representative is authorized to access.
3. The Department Representative selects a request from the list.
4. The system retrieves the selected request's information.
5. The system displays purpose, category, specifications, quantity, preferred condition, urgency, destination, required date, selected asset if any, current status, decision reason if applicable, and linked reservation and transfer references.
6. The Department Representative reviews the request information.
Alternative Flows
A1 No Resource Requests
At step 2, the system finds no resource requests accessible to the Department Representative.
The system displays a message indicating that no requests are available.
Exception Flows
E1 Request Not Found
At step 4, the selected request no longer exists or cannot be retrieved.
The system displays an error message and allows the Department Representative to return to the request list.
E2 Unauthorized Access
The Department Representative attempts to view a request they do not have permission to access.
The system denies access and displays an appropriate error message.
7.5.3 Update Resource Request
Use Case ID: UC-25
Use Case Name: Update Resource Request
Related Requirement: FR-5: Resource Requests
Detailed Requirements: FR-5.2 through FR-5.6; FR-5.12 through FR-5.20
Primary Actor: Department Representative
Goal: Allow the Department Representative to update an existing resource request to ensure that its details accurately reflect the department's needs.
Preconditions: The representative is authenticated and authorized for the request. The request is Pending Approval and has no active reservation or transfer.
Trigger: The Department Representative navigates to the Resource Requests section.
Postconditions: The updated resource request information is successfully saved in the system. The Department Representative receives a confirmation pop-up notification and an email confirming that the resource request has been updated successfully.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Department Representative navigates to the Resource Requests section.
2. The system displays the resource requests that the Department Representative is authorized to access.
3. The Department Representative selects a request and clicks Edit Request.
4. The system checks that the request is Pending Approval, belongs to an authorized department, and has no active reservation or transfer.
5. The system displays the request's current information.
6. The representative modifies permitted request fields and may select or change the linked asset.
7. The Department Representative submits the updated information.
8. The system rechecks status, authorization, and field validity, then saves the changes with the responsible user and timestamp while retaining earlier details in audit history.
9. The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1 Update Cancelled
The Department Representative cancels the update.
The system keeps the original request information unchanged.
Exception Flows
E1 Invalid Information
At step 8, the system detects missing or invalid information.
The system displays an error message and asks the Department Representative to correct the information.
E2 Request Cannot Be Modified
At step 4 or 8, the request is no longer Pending Approval or has an active reservation or transfer. The system blocks the update and preserves the saved record.
E3 Unauthorized Update
The Department Representative does not have permission to modify the selected request.
The system denies the update and displays an appropriate error message
E4 Saving Failure
When the submitted operation is saved, storage fails. The system reports the failure, preserves the previous saved records, and allows a retry after current data and authority are rechecked.
E5 Confirmation Email Not Delivered
After the core record is successfully saved, confirmation email delivery fails. The system keeps the saved result, informs the actor of the delivery failure, and retains the on-screen confirmation; the user must not repeat the original operation merely to obtain email.
7.5.4 Cancel Pending Resource Request
Use Case ID: UC-50
Use Case Name: Cancel Pending Resource Request
Related Requirement: FR-5 Resource Requests
Detailed Requirements: FR-5.18; FR-5.21 through FR-5.23
Primary Actor: Department Representative
Goal: Cancel an unapproved request without affecting reserved stock.
Preconditions: The representative is authenticated and authorized for a Pending Approval request with no reservation or transfer.
Trigger: The representative selects Cancel Request.
Postconditions: The request is Cancelled with its reason, actor and timestamp; no asset quantity is released because no reservation existed.
Failure Postconditions: The previous request, proposal, asset and allocation records remain unchanged if authorization, validation or saving fails.
Main Success Scenario
1. The representative opens a Pending Approval request and selects Cancel Request.
2. The system displays the request and asks for a cancellation reason and confirmation.
3. The representative supplies the reason and confirms.
4. The system rechecks current authority and Pending Approval status and that no active reservation or transfer exists.
5. The system saves cancellation and its audit event together and displays confirmation.
Alternative Flows
A1 Cancellation Abandoned
Before step 3, the user cancels; the request remains unchanged.
Exception Flows
E1 Approval Occurred Concurrently
At step 4, the request is now Approved or a reservation exists. The system blocks this cancellation and directs the user to the reservation cancellation workflow.
E2 Unauthorized Missing Reason or Failed Save
The system denies unauthorized cancellation, requests a missing reason or rolls back a failed save without changing asset quantities.
7.6 Reservation Management
Rules: Only approval creates an Active reservation. Approval, quantity allocation, and reservation creation are one operation. Cancellation is allowed only before dispatch and releases quantity once. Receipt confirmation alone fulfils the reservation.

Example: View a two-monitor reservation, cancel it before dispatch, or inspect its recorded history.
7.6.1 View Reservation
Use Case ID: UC-29
Use Case Name: View Reservation
Related Requirement: FR-6: Reservation Management
Detailed Requirements: FR-6.7 through FR-6.9; FR-6.20
Primary Actor: Authorized User — Department Representative or Asset Custodian
Goal: Allow an authorized user to view an asset reservation and its current status.
Preconditions: The user is logged in and has permission to access the reservation. The reservation exists and is linked to an approved asset request.
Trigger: The user navigates to the Reservations section.
Postconditions: The system displays the reservation information without modifying its status or the asset quantities.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user navigates to the Reservations section.
2. The system displays the reservations the user is authorized to access.
3. The user selects a reservation.
4. The system retrieves the selected reservation.
5. The system displays the reservation ID, associated request ID, asset name, reserved quantity, requesting department, creation date, and status.
6. The user reviews the reservation information.
Alternative Flows
A1 No Reservations
At step 2, the system finds no accessible reservations.
The system displays a message indicating that no reservations are available.
Exception Flows
E1 Reservation Not Found
At step 4, the selected reservation cannot be found.
The system displays an error message and allows the user to return to the reservation list.
E2 Unauthorized Access
The user attempts to access a reservation outside their permissions.
The system denies access and displays an appropriate error message.
E3 Retrieval Failure
At step 4, the reservation information cannot be retrieved.
The system displays an error message and allows a retry.
7.6.2 Cancel Reservation
Use Case ID: UC-30
Use Case Name: Cancel Reservation
Related Requirement: FR-6: Reservation Management
Detailed Requirements: FR-6.10 through FR-6.15; FR-6.19; FR-6.20
Primary Actor: Authorized User — Department Representative or Asset Custodian
Goal: Allow an authorized user to cancel an active reservation before dispatch and release its reserved quantity.
Preconditions: The user is logged in and has cancellation permission. The reservation is active, and the associated assets have not been dispatched.
Trigger: The user opens an active reservation.
Postconditions: The reservation is marked Cancelled, its quantity is released once, and the cancellation reason, actor, and timestamp are recorded. The associated request is marked Cancelled.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The user opens an active reservation.
2. The user selects Cancel Reservation.
3. The system displays the reservation details and requests a cancellation reason.
4. The user enters the reason and confirms cancellation.
5. The system verifies the user’s permission, reservation status, and dispatch status.
6. The system saves the Cancelled reservation, Cancelled request, released quantity, cancellation reason, responsible user, and timestamp as one operation.
7. The system makes the resulting request and reservation status available to authorized users without releasing the quantity again.
8. The system displays a confirmation message.
Alternative Flows
A1 Cancellation Abandoned
At step 4, the user cancels the action.
The reservation and asset quantities remain unchanged.
A2 Missing Cancellation Reason
At step 5, the system detects that no reason was provided.
The system asks the user to enter a reason before continuing.
A3 Assets Already Dispatched
At step 5, the system detects that dispatch has occurred.
The system blocks cancellation and explains that the transfer must be resolved through the appropriate recovery process.
A4 Reservation Already Cancelled or Fulfilled
At step 5, the reservation is no longer active.
The system displays its current status and does not release any quantity.
Exception Flows
E1 Saving Failure
At step 6, the cancellation cannot be saved.
The system reports the failure and preserves the previous request status, reservation status, and asset quantities.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.6.3 View Reservation History
Use Case ID: UC-31
Use Case Name: View Reservation History
Related Requirement: FR-6: Reservation Management
Detailed Requirements: FR-6.17; FR-6.18; FR-6.20
Primary Actor: Authorized User — Department Representative or Asset Custodian
Goal: Allow an authorized user to review the recorded history of a reservation.
Preconditions: The user is logged in and has permission to access the reservation. A reservation record exists.
Trigger: The user opens a reservation.
Postconditions: The system displays recorded reservation events without changing stored information.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user opens a reservation.
2. The user selects View History.
3. The system retrieves the reservation’s recorded events.
4. The system displays creation, cancellation, or fulfilment events in chronological order.
5. The system displays each event’s action, responsible actor, timestamp, and reason where applicable.
6. The user reviews the history.
Alternative Flows
A1 No Subsequent Status Changes
At step 3, the reservation has no events after creation.
The system displays the creation record and current status.
Exception Flows
E1 Unauthorized Access
The user does not have permission to access the history.
The system denies access.
E2 History Retrieval Failure
At step 3, the history cannot be retrieved.
The system displays an error message and allows a retry.
7.7 Approval Management
Rules: The responsible custodian acts as authorized approver and cannot decide their own request. A decision requires Pending Approval status. Availability is rechecked when approval is saved; approval does not change custody or location.

Example: Approve a request for two available monitors or reject it with a recorded reason.
7.7.1 View Pending Requests
Use Case ID: UC-32
Use Case Name: View Pending Requests
Related Requirement: FR-7: Approval Management
Detailed Requirements: FR-7.1 through FR-7.3; FR-7.18
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to view pending requests for assets under their responsibility.
Preconditions: The Asset Custodian is logged in and has authority over the relevant assets.
Trigger: The Asset Custodian navigates to the Approval Management section.
Postconditions: The system displays pending request information without changing request status or reserving assets.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The Asset Custodian navigates to the Approval Management section.
2. The system retrieves Pending Approval requests linked to assets under the custodian's responsibility and eligible for independent review.
3. The system displays the pending request list.
4. The Asset Custodian selects a request.
5. The system displays the requester, asset, quantity, purpose, destination, required date, and current availability.
6. The Asset Custodian reviews the request details.
Alternative Flows
A1 No Pending Requests
At step 2, no pending requests are found.
The system displays a message indicating that no requests require review.
A2 Request Already Processed
At step 5, the selected request is no longer pending.
The system displays its current status and prevents another decision.
Exception Flows
E1 Unauthorized Access
The Asset Custodian attempts to view a request outside their authority.
The system denies access.
E2 Retrieval Failure
The system cannot retrieve the request information.
The system displays an error message and allows a retry.
7.7.2 Approve Asset Request
Use Case ID: UC-33
Use Case Name: Approve Asset Request
Related Requirement: FR-7: Approval Management
Detailed Requirements: FR-7.4 through FR-7.12; FR-7.15 through FR-7.18; FR-6.1 through FR-6.6
Primary Actor: Asset Custodian
Goal: Allow the responsible Asset Custodian to approve a pending request and reserve the requested quantity.
Preconditions: The Asset Custodian is logged in, has authority over the asset, and is not the requester. The request is pending approval.
Trigger: The Asset Custodian opens a pending request.
Postconditions: The request is marked Approved, a linked reservation is created, and the available quantity is reduced by the reserved quantity. The reviewer and decision timestamp are recorded. Asset ownership and location remain unchanged.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian opens a pending request.
2. The system displays the request details and current availability.
3. The Asset Custodian selects Approve and confirms the decision.
4. The system rechecks reviewer authority and separation from the requester, Pending Approval status, linked asset eligibility and publication, positive whole-number quantity, and current unreserved availability.
5. The system saves Approved status, creates one linked Active reservation, and allocates the requested quantity as one operation.
6. The system records the reviewer and decision timestamp.
7. The system displays confirmation and makes the approved status available to the requester.
Alternative Flows
A1 Insufficient Availability
At step 4, the requested quantity exceeds current availability.
The system blocks approval, explains the shortage, and leaves the request pending.
A2 Request Already Processed
At step 4, another decision has already been saved.
The system displays the current status and creates no additional reservation.
A3 Approval Abandoned
At step 3, the Asset Custodian cancels confirmation.
The request remains pending.
Exception Flows
E1 Self-Approval Attempt
At step 4, the reviewer is identified as the requester.
The system blocks approval.
E2 Saving Failure
At step 5, approval or reservation creation cannot be saved.
Neither operation takes effect. The request remains pending, and quantities remain unchanged.
E3 No Selected Asset or Asset Ineligible
At step 4, the request has no valid selected asset or that asset no longer permits allocation. The system blocks approval and leaves the request Pending Approval.
E4 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.7.3 Reject Asset Request
Use Case ID: UC-34
Use Case Name: Reject Asset Request
Related Requirement: FR-7: Approval Management
Detailed Requirements: FR-7.4 through FR-7.6; FR-7.12 through FR-7.15; FR-7.17; FR-7.18
Primary Actor: Asset Custodian
Goal: Allow the responsible Asset Custodian to reject a pending request and record the reason.
Preconditions: The custodian is authenticated, has authority over the linked asset, and is not the requester. The request is Pending Approval.
Trigger: The Asset Custodian opens a pending request.
Postconditions: The request is marked Rejected. The reason, reviewer, and timestamp are recorded. No reservation is created, and asset quantities remain unchanged.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The Asset Custodian opens a pending request.
2. The system displays its details.
3. The Asset Custodian selects Reject.
4. The system requests a rejection reason.
5. The Asset Custodian enters the reason and confirms.
6. The system rechecks authority, separation from the requester, Pending Approval status, and the nonblank rejection reason.
7. The system saves the rejection, reason, reviewer, and timestamp.
8. The system displays confirmation and makes the decision available to the requester.
Alternative Flows
A1 Missing Reason
At step 6, the rejection reason is missing.
The system asks the Asset Custodian to provide a reason.
A2 Rejection Abandoned
At step 5, the Asset Custodian cancels the action.
The request remains pending.
A3 Request Already Processed
At step 6, the request is no longer pending.
The system displays its current status and blocks rejection.
Exception Flows
E1 Unauthorized Decision
At step 6, the custodian lacks authority over the asset.
The system denies the operation.
E2 Saving Failure
At step 7, the decision cannot be saved.
The request remains pending, and the system reports the failure.
E3 Self Decision Attempt
At step 6, the custodian is the requester. The system denies the rejection and leaves the request Pending Approval for an independent reviewer.
7.8 Transfer Management
Rules: The transfer states are Awaiting Dispatch, In Transit, and Completed. Failed delivery remains In Transit; discrepancies block completion. Receipt, fulfilment, custody, location, and life-cycle history are committed together. Source reserved quantities must not be allocated twice.

Example: Dispatch two monitors, record an unsuccessful delivery if necessary, and confirm the full quantity only after receipt.
7.8.1 Record Asset Dispatch
Use Case ID: UC-35
Use Case Name: Record Asset Dispatch
Related Requirement: FR-8: Transfer Management
Detailed Requirements: FR-8.1 through FR-8.7; FR-8.18 through FR-8.20; FR-8.21
Primary Actor: Facilities Department Personnel
Goal: Allow authorized Facilities Department personnel to record dispatch of reserved assets to the requesting department.
Preconditions: Facilities personnel are logged in and authorized. The request is approved, its reservation is active, and source and destination details are recorded. The assets have not already been dispatched.
Trigger: Facilities personnel navigate to the Transfer Management section.
Postconditions: Dispatch details and the timestamp are saved. The transfer is marked In Transit. The reservation remains active, and destination location and custody are not yet updated.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. Facilities personnel navigate to the Transfer Management section.
2. The system displays approved requests with active reservations awaiting dispatch.
3. Facilities personnel select a request.
4. The system displays the linked request, reservation, asset, reserved quantity, source and destination; Facilities personnel enter or verify collection or delivery arrangements and supporting documents if supplied.
5. Facilities personnel verify the details and confirm dispatch.
6. The system rechecks authority, approval, Active reservation, Awaiting Dispatch status, source and destination, recorded condition and maintenance eligibility, and that the dispatch quantity equals the reserved quantity.
7. The system saves dispatch details, arrangements, responsible personnel, timestamp, and In Transit status as one operation.
8. The system displays confirmation while retaining the Active reservation and existing custody and location.
Alternative Flows
A1 Invalid Transfer Quantity
At step 6, the quantity is invalid or exceeds the reservation.
The system blocks dispatch and requests correction.
A2 Reservation No Longer Active
At step 6, the reservation has been cancelled or fulfilled.
The system blocks dispatch.
A3 Dispatch Abandoned
At step 5, Facilities personnel cancel the action.
The transfer remains awaiting dispatch.
A4 Dispatch Already Recorded
At step 6, dispatch has already been saved.
The system displays the current transfer status and does not record duplicate dispatch.
Exception Flows
E1 Saving Failure
At step 7, dispatch cannot be saved.
The system reports failure and preserves the previous transfer state.
E2 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.8.2 View Transfer Status
Use Case ID: UC-36
Use Case Name: View Transfer Status
Related Requirement: FR-8: Transfer Management
Detailed Requirements: FR-8.8; FR-8.9; FR-8.19; FR-8.20
Primary Actor: Authorized User — Facilities Department Personnel or Receiving Department Representative
Goal: Allow authorized users to track an asset transfer and review recorded delivery events.
Preconditions: The user is logged in, a transfer record exists, and the user has permission to access it.
Trigger: The user navigates to the Transfers section.
Postconditions: Transfer information is displayed without changing its status or asset quantities.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The user navigates to the Transfers section.
2. The system displays transfers the user is authorized to access.
3. The user selects a transfer.
4. The system retrieves the transfer details.
5. The system displays the transfer ID, asset, quantity, source, destination, status, and recorded dispatch and receipt times.
6. The system displays recorded delivery attempts and discrepancies, where applicable.
7. The user reviews the information.
Alternative Flows
A1 No Accessible Transfers
At step 2, no transfers are found.
The system displays an appropriate message.
A2 Unsuccessful Delivery Recorded
At step 6, a failed delivery attempt exists.
The system displays its reason and time. The transfer remains incomplete.
Exception Flows
E1 Unauthorized Access
The user attempts to access an unauthorized transfer.
The system denies access.
E2 Retrieval Failure
At step 4, transfer information cannot be retrieved.
The system displays an error message and allows a retry.
7.8.3 Confirm Asset Receipt
Use Case ID: UC-37
Use Case Name: Confirm Asset Receipt
Related Requirement: FR-8: Transfer Management
Detailed Requirements: FR-8.10 through FR-8.14; FR-8.18 through FR-8.20; FR-6.16
Primary Actor: Receiving Department Representative
Goal: Allow the receiving representative to confirm delivery and complete the asset transfer.
Preconditions: The representative is logged in and authorized for the destination department. Dispatch is recorded, the transfer is In Transit, and the reservation remains active.
Trigger: The receiving representative opens an incoming transfer.
Postconditions: The receipt and receiving user are recorded, the transfer is Completed, the reservation and request are Fulfilled, custody and destination location are updated, and one linked life-cycle event is saved. The source quantity cannot be allocated again.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. The receiving representative opens an incoming transfer.
2. The system displays the asset, dispatched quantity, source, and destination.
3. The representative checks the delivered assets and enters the received quantity.
4. The representative confirms receipt.
5. The system verifies authorization, transfer status, and that the received quantity matches the dispatched quantity.
6. The system prepares the receipt, receiving representative, and timestamp for the completion operation.
7. The system saves receipt, Completed transfer, Fulfilled reservation and request, receiving-department custody and location for the received reserved units, and their linked life-cycle event as one operation. Untransferred source units remain unchanged.
8. The system displays confirmation.
Alternative Flows
A1 Quantity Discrepancy
At step 5, the received quantity differs from the dispatched quantity.
The system records the discrepancy and blocks completion until an authorized person resolves it.
A2 Receipt Confirmation Abandoned
At step 4, the representative cancels the action.
The transfer remains In Transit.
A3 Transfer Already Completed
At step 5, receipt has already been confirmed.
The system displays the completed status and performs no further quantity or location updates.
Exception Flows
E1 Unauthorized Confirmation
At step 5, the user lacks authority for the destination department.
The system blocks confirmation.
E2 Saving Failure
At steps 6–7, the completion operation cannot be saved.
The system reports the failure and preserves the previous receipt, transfer, reservation, location, and custody records.
7.8.4 Record Delivery Attempt and Resolve Discrepancy
Use Case ID: UC-38
Use Case Name: Record Delivery Attempt and Resolve Discrepancy
Related Requirement: FR-8: Transfer Management
Detailed Requirements: FR-8.12; FR-8.15 through FR-8.20
Primary Actor: Facilities Department Personnel
Supporting Actor: Receiving Department Representative when confirming discrepancy resolution
Goal: Record unsuccessful delivery attempts, revised arrangements, and supported discrepancy corrections without prematurely completing a transfer.
Preconditions: The user is authenticated and authorized for an In Transit transfer with an Active reservation. A discrepancy must exist before it can be corrected.
Trigger: Facilities personnel open an authorized In Transit transfer and select Record Delivery Attempt.
Postconditions: The attempt or correction is saved with its reason, evidence where supplied, user, and timestamp. The original discrepancy remains in history; the transfer remains In Transit and receipt completion still requires UC-37.
Failure Postconditions: If validation, authorization, confirmation, or saving fails, no partial operation is committed and the previous saved records remain unchanged.
Main Success Scenario
1. Facilities personnel open an authorized In Transit transfer and select Record Delivery Attempt.
2. The system displays the transfer, arrangements, and any unresolved discrepancies.
3. Facilities personnel enter the outcome, reason, event time, and revised arrangements or supporting discrepancy-correction details.
4. For a discrepancy correction, the receiving representative verifies the corrected delivery information.
5. The user submits the record.
6. The system validates authority, In Transit status, required reason and details, and supporting receiver verification when correcting a discrepancy.
7. The system appends the attempt or correction with a recording timestamp and user, preserving the original event and retaining the Active reservation.
8. The system displays confirmation; successful receipt is subsequently confirmed through UC-37.
Alternative Flows
A1 Entry Cancelled
Before step 5, the user cancels. No delivery-attempt or correction record is saved.
Exception Flows
E1 Invalid or Incomplete Details
At step 6, a reason or required correction detail is missing. The system identifies the problem and requires correction before saving.
E2 Transfer Already Completed
At step 6, the transfer is no longer In Transit. The system blocks the update and displays its current state.
E3 Saving Failure
At step 7, the save fails. The system reports failure and preserves all previous transfer, discrepancy, reservation, quantity, and custody records.
E4 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
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
7.12 AI Based Resource Matching
Rules: The matching module is internal. Hard quantity and mandatory-specification constraints apply before ranking suitable candidates. Display compatibility from 0 to 100, where 100 is the strongest compatibility on the defined model scale; this value is not a probability or AI confidence. Explain the suitability factors used. Selecting a match follows the resource-request workflow and never automatically creates a reservation.

Example: Match a request for a display screen with a listing described as a monitor and inspect the compatibility explanation.
7.12.1 Generate AI Resource Matches
Use Case ID: UC-26
Use Case Name: Generate AI Resource Matches
Related Requirement: FR-12: AI-Based Resource Matching
Detailed Requirements: FR-12.1 through FR-12.11; FR-12.15; FR-12.17 through FR-12.20
Primary Actor: Department Representative
Goal: Allow the Department Representative to use AI to identify available campus assets that match a departmental resource request based on compatibility, condition, quantity, location, and urgency.
Preconditions: The representative is authenticated, authorized for the request, and the request is Pending Approval. Input sufficiency is validated before analysis.
Trigger: The Department Representative navigates to the Resource Requests section.
Postconditions: The system generates and displays recommended asset matches for review. No asset is reserved or transferred automatically.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The Department Representative navigates to the Resource Requests section.
2. The Department Representative selects an open resource request.
3. The Department Representative clicks Generate AI Matches.
4. The system validates current request details and retrieves accessible published assets with their unreserved quantities and recorded condition, specifications, location, and available cost and sustainability data.
5. The internal AI matching module compares meaning and suitability using category, purpose, specifications, quantity, condition, location, urgency, required date, and available cost and environmental information; it excludes candidates failing mandatory requirements.
6. The system ranks suitable assets and stores an identified result set with its timestamp, request reference, and input snapshot or versions.
7. The system displays recommended assets, compatibility scores on a stated 0 to 100 scale, explanations, separate confidence information when available, and limitations of any estimated benefits.
8. The Department Representative reviews the recommendations.
Alternative Flows
A1 No Suitable Matches
At step 5, the AI cannot identify suitable available assets.
The system displays a message indicating that no suitable matches are currently available.
The Department Representative can search for assets manually or try again later.
A2 Insufficient Request Information
At step 5, the AI cannot generate suitable recommendations because the request information is insufficient.
The system asks the Department Representative to provide additional request details.
Exception Flows
E1 AI Matching Unavailable
At step 5, the AI matching module is unavailable or fails to process the request.
The system displays an error message and allows the Department Representative to search and filter assets manually.
E2 Result Set Cannot Be Saved
When generated results are saved, the operation fails. The system reports the error, retains previous result sets and the selected request asset, and does not present the failed operation as a successfully saved new result set.
E3 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
7.12.2 Review AI Resource Matches
Use Case ID: UC-27
Use Case Name: Review AI Resource Matches
Related Requirement: FR-12: AI-Based Resource Matching
Detailed Requirements: FR-12.8 through FR-12.13; FR-12.15; FR-12.16; FR-12.19; FR-12.20
Primary Actor: Department Representative
Goal: Allow the Department Representative to review AI-recommended asset matches and determine whether they are suitable for the department's resource request.
Preconditions: The Department Representative is logged into the system and has permission to access the selected request. The system has successfully generated recommended asset matches.
Trigger: The Department Representative selects a recommended asset.
Postconditions: The Department Representative has reviewed the recommended assets and their suitability. Reviewing a recommendation does not reserve an asset or approve a transfer.
Failure Postconditions: No stored asset, request, reservation, transfer, or recommendation information is changed if access or retrieval fails.
Main Success Scenario
1. The system displays the AI-recommended asset matches.
2. The Department Representative selects a recommended asset.
3. The system rechecks permission, current publication, available quantity, and whether the match is based on current relevant information.
4. The system displays current asset details, score scale, match explanation, confidence when available, and any estimate limitations.
5. The Department Representative compares the asset's specifications, condition, quantity, and location with the departmental requirements.
6. The Department Representative determines whether the asset is suitable.
7. The representative returns to the result list or uses the permitted resource-request update workflow to select a suitable asset; review itself makes no reservation.
Alternative Flows
A1 Recommendation Unsuitable
At step 6, the Department Representative determines that the recommended asset does not meet the department's needs.
The Department Representative returns to the recommendation list and reviews another asset.
A2 Asset No Longer Available
At step 3, the recommended asset has been unpublished or is no longer available.
The system informs the Department Representative that the asset is unavailable and returns to the recommendation list.
A3 Review Cancelled
The Department Representative cancels the review.
The system returns to the resource request without modifying the request or any asset records.
Exception Flows
E1 Unauthorized Access
At step 3, the Department Representative does not have permission to view the recommended asset.
The system denies access and displays an appropriate error message.
E2 Retrieval Failure
When the system retrieves the selected information, the operation fails. The system reports the failure and allows a return to the list or a retry without changing any stored record.
7.12.3 Regenerate AI Resource Matches
Use Case ID: UC-28
Use Case Name: Regenerate AI Resource Matches
Related Requirement: FR-12: AI-Based Resource Matching
Detailed Requirements: FR-12.1 through FR-12.11; FR-12.14; FR-12.15; FR-12.17 through FR-12.20
Primary Actor: Department Representative
Goal: Allow the Department Representative to request new AI-generated resource matches when the initial recommendations are unsuitable or the request details or available assets have changed.
Preconditions: The representative is authenticated and authorized for a Pending Approval request, and a previous matching attempt exists.
Trigger: The Department Representative clicks Regenerate Matches.
Postconditions: The system generates and displays an updated set of recommended asset matches based on the current request information and available assets. No asset is reserved or transferred automatically.
Failure Postconditions: Any failed generation or application leaves the saved asset and request records and previously accepted form values unchanged; manual entry or search remains available.
Main Success Scenario
1. The Department Representative reviews the initial AI-generated resource matches.
2. The Department Representative determines that updated recommendations are needed.
3. The Department Representative updates and saves the resource request details if required.
4. The Department Representative clicks Regenerate Matches.
5. The system validates the latest saved Pending Approval request and retrieves currently accessible published assets and their unreserved quantities.
6. The internal AI module compares current candidates using the same suitability factors and mandatory constraints used for initial generation.
7. The system saves and displays a new identified, timestamped ranked result set with scores, explanations, and data limitations while retaining earlier sets and the currently selected asset.
8. The Department Representative reviews the updated recommendations.
Alternative Flows
A1 No Suitable Matches
At step 6, the AI cannot identify suitable available assets.
The system displays a message indicating that no suitable matches are currently available.
The Department Representative can search for assets manually or try again later.
A2 Insufficient Request Information
At step 6, the AI cannot generate suitable recommendations because the request information is insufficient.
The system asks the Department Representative to provide additional request details.
A3 Regeneration Cancelled
Before regeneration is submitted, the Department Representative cancels the process.
The system retains the previously displayed recommendations without generating new matches.
Exception Flows
E1 AI Matching Unavailable
At step 6, the AI matching module is unavailable or fails to process the request.
The system displays an error message and allows the Department Representative to search and filter assets manually.
E2 Result Set Cannot Be Saved
When generated results are saved, the operation fails. The system reports the error, retains previous result sets and the selected request asset, and does not present the failed operation as a successfully saved new result set.
E3 Unauthorized Action
Before protected information is displayed or an operation is saved, the system rechecks authentication and authority. It denies unauthorized access or action and preserves all saved records.
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
Appendix A Glossary
Term	Definition
SRS	Software Requirements Specification.
FR	Functional requirement stating a capability or system response.
NFR	Non-functional requirement describing quality or operating constraints.
UC	Use case describing an actor goal and its interactions.
UML	Unified Modeling Language.
AI	Artificial intelligence used for advisory classification, matching or summaries.
LLM	Large language model supporting natural-language assistance.
RBAC	Role-based access control, combined here with departmental scope.
Custody	Responsibility for the physical asset, updated through authorized receipt.
Asset Life Cycle	Events from registration and acquisition through use, maintenance and end-of-life handling.
Waste Diversion	Documented material kept out of final disposal through defined recovery routes.
Avoided Purchase	A documented departmental need satisfied by reuse instead of buying an equivalent new asset.
kg CO2e	Kilograms of carbon dioxide equivalent; the unit used for documented emission estimates.
Compatibility	A stated matching score; it is distinct from AI confidence.
TBD	A decision or evidence item to be determined during design or stakeholder review.

