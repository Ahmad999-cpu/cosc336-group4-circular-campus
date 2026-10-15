Contribution:
Sections 1 full, section 2 full, section 3 full, 4.1, 4.2, 4.3, section 5 full, section 6 full, 7.1, 7.2, 7.3, appendix A full, Appendix B full, Appendix C full
Section 1: Introduction
1.1 Purpose
The purpose of this Software Requirements Specification (SRS) document is to define the functional and non-functional requirements of the Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System. This document outlines the system's expected behavior, user roles, permissions, business rules, and sustainability objectives. It also includes a comprehensive UML use case diagram and detailed use case descriptions to support the upcoming design, development, and testing phases.
1.2 Document Conventions
This document follows the Software Requirements Specification (SRS) structure provided in the COSC 336 project guidelines. Functional requirements are identified using FR, non-functional requirements using NFR, business rules using BR, and use cases using UC. Requirements are written using "The system shall" to ensure clarity and testability. System features are assigned High, Medium, or Low priorities, which apply to their associated functional requirements unless otherwise specified.
1.3 Intended Audience and Reading Suggestions
This document is intended for project developers, instructors, stakeholders, testers, and future system users. Readers should begin with the introduction and overall system description, followed by the external interface requirements, functional and non-functional requirements, and business rules. The detailed use case descriptions and UML diagram provide additional information about system interactions and expected workflows.
1.4 Product Scope
The Circular Campus system aims to improve the management and reuse of university assets by allowing departments to register, publish, search, request, reserve, transfer, and maintain available resources. AI-powered features support asset classification, resource matching, and sustainability recommendations, while human users retain control over important decisions. The system aims to reduce unnecessary purchases, extend asset life cycles, minimize waste, and improve resource allocation across the university.

1.5 AI declaration:

AI tools were used to assist in identifying potentially overlooked functional requirements, use cases, and alternative flows to ensure the completeness of our requirements analysis. Additionally, AI was used to generate UML use case diagrams based on descriptions and instructions provided by our team, including the identification of actors, their interactions, and relationships between use cases. AI assisted with drafting, consistency checks and UML diagrams. The team remains responsible for reviewing the final requirements and diagrams before submission.
The asset reuse rate equation was found by chatGPT.


1.6 References:
1. Intelligent AI-powered circular campus Phase 1 Initial Plan and Requirement Gathering Document
2. Intelligent AI-powered circular campus Phase 2 Feasibility Study
3. Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle
 Management System, Project Description
4. Software Requirements Specification (SRS) Template – Included in the Appendix of the COSC 336 Project Description.
5. Functional and Non-Functional Requirements – COSC 336 Requirements Exercises.
6. Use Case Writing Exercises – COSC 336.
7. United Arab Emirates. Federal Decree-Law No. 45 of 2021 Concerning the Protection of Personal Data. UAE Legislation. https://uaelegislation.gov.ae/en/legislations/1972
8. United Arab Emirates. Federal Law No. 12 of 2018 on Integrated Waste Management. UAE Legislation. https://uaelegislation.gov.ae/en/legislations/1164
9. United Arab Emirates. Federal Decree-Law No. 34 of 2021 on Countering Rumors and Cybercrimes, as amended. UAE Legislation. https://uaelegislation.gov.ae/en/legislations/1526


Section 2: Overall description
2.1 Product Perspective
The Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System is a proposed web-based platform designed to improve resource sharing and asset management across Khalifa University. Rather than replacing an existing system, it is designed as a centralized solution that combines traditional asset management functions with AI-powered classification, resource matching, and sustainability recommendations. The system aims to connect university departments through a shared platform, reducing resource waste and improving the utilization of existing campus assets.
2.2 Product functions:


The feature number identifies its location in this report; the FR number retains the original requirement identity. Reporting uses feature 13 to match the team's final numbering. Authentication and the assistant are features 14 and 15. Priorities follow the Phase 2 prototype scope; advanced AI reporting and the assistant may be deferred while conventional operations remain available.
Sec.	Feature	FR	Priority	Count
4.1	Asset Registration	FR-2	High	17
4.2	Asset Publication	FR-3	High	19
4.3	AI Assisted Asset Classification	FR-11	Medium	24
4.4	Asset Search and Filtering	FR-4	High	17
4.5	Resource Requests	FR-5	High	23
4.6	Reservation Management	FR-6	High	20
4.7	Approval Management	FR-7	High	18
4.8	Transfer Management	FR-8	High	21
4.9	Asset Life Cycle Tracking	FR-9	High	22
4.10	Maintenance and Repair Tracking	FR-10	High	20
4.11	Sustainability Recommendations	FR-13	Medium	20
4.12	AI Based Resource Matching	FR-12	Medium	20
4.13	Reporting	FR-15	Mixed	17
4.14	Authentication and Access Control	FR-1	High	17
4.15	LLM Powered Assistant	FR-14	Low	16
2.3 Actors, and their concerns: 

Actor or Component	Role and Permissions	Main Concerns
Asset Custodian and assigned Approver	Manage assigned assets; review requests and independently assigned end-of-life proposals.	Accurate stock, accountable decisions and custody.
Lecturer or Departmental Administrator	Use only the roles and asset scopes explicitly assigned; no automatic inheritance of custodian privileges.	Suitable resources and clear permissions.
Department Representative	Search, submit or cancel departmental requests, view reservations and confirm receipt.	Availability, delivery and departmental scope.
Facilities Department Personnel	Dispatch approved reserved assets and record delivery attempts and discrepancy resolutions.	Safe, traceable transfers.
Maintenance Staff	Inspect assigned assets, record repairs, costs, condition and maintenance progress.	Reliable condition and service records.
Sustainability Officer	Review sustainability advice and permitted sustainability reports.	Reuse, defensible environmental estimates.
Procurement Officer	Review permitted availability, request and purchasing-related reports.	Avoiding duplicate purchases.
Finance Officer	View permitted valuation, costs, financial and savings reports.	Correct units, evidence and access scope.
System Administrator	Manage accounts and roles and review security logs; business approvals require a separately assigned role.	Access control and audit integrity.
External AI Services	Support classification, sustainable-action advice, assistant answers or report summaries where integrated.	Restricted context, explainability and service failure.
Internal AI Matching Module	Computes ranked matches as a component inside the system, not an external UML actor.	Compatibility and current permitted data.
Email Delivery Service	Delivers configured confirmation messages after successful business operations.	Delivery failures do not roll back a saved record.
2.4 Operating Environment
The system is designed to operate as a web-based application accessible through modern browsers such as Google Chrome, Microsoft Edge, and Mozilla Firefox on computers and laptops. It requires a stable internet connection and a hosting environment capable of supporting application services, database storage, and AI-powered functionalities. The system shall communicate securely with its database and integrated AI services through appropriate network protocols.
2.5 Design and Implementation Constraints
The system shall comply with university security and privacy policies to protect sensitive user and asset information. Development shall follow a modular architecture to support maintainability and future expansion. The system shall implement role-based access control, secure communication protocols, and appropriate data validation. AI-generated recommendations shall remain advisory, with final decisions requiring authorization from responsible personnel. The system's implementation will also be constrained by the development timeline, available technical resources, and access to university asset data.
2.6 User Documentation
The system shall provide user documentation to assist university staff in understanding and operating its main functions. Documentation shall include instructions for asset registration, publication, resource requests, reservations, approvals, transfers, maintenance tracking, and AI-assisted features. User guides, frequently asked questions, and basic troubleshooting instructions shall be made available electronically to support users with different levels of technical experience.
2.7 Assumptions and Dependencies
The system assumes that authorized university personnel will have access to compatible devices, reliable internet connectivity, and accurate asset information. Its functionality depends on the availability of database services, hosting infrastructure, and external AI services for classification and recommendations. The effectiveness of AI-generated results and sustainability measurements will depend on the quality and completeness of available data. If AI services become unavailable, users shall still be able to perform essential asset management operations through manual or conventional alternatives.

Section 3: External Interface Requirements
This section describes how the Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System interacts with users, hardware devices, external software services, and communication networks. These interfaces ensure accessibility, secure data exchange, and effective integration between traditional asset management functions and AI-powered services.
3.1 User Interfaces
The system shall provide a user-friendly web interface accessible through standard web browsers. The interface shall include login pages, asset registration forms, resource search and filtering, request management, approval workflows, maintenance tracking, and sustainability dashboards. Users shall interact with AI-powered features through classification recommendations, resource matching results, and a natural-language assistant. The interface shall provide clear navigation, confirmation notifications, and error messages.
3.2 Hardware Interfaces
The system shall be accessible through university computers, laptops, and other compatible devices with an internet connection and a modern web browser. No specialized hardware shall be required for standard system operations. The application shall communicate with its hosting infrastructure and database servers to process requests and retrieve stored information.
3.3 Software Interfaces
The system shall interact with a database management system to store and retrieve asset records, user accounts, resource requests, reservations, transfers, and maintenance information. It shall also integrate with AI services for asset classification, resource matching, sustainability recommendations, and natural-language assistance. These services shall exchange information through defined application interfaces while maintaining appropriate access controls.
3.4 Communications Interfaces
The system shall use HTTPS to ensure secure communication between users and the application. It shall support email notifications for important activities, including asset registration, publication, request updates, and approvals. Communication with AI services and other integrated components shall use secure APIs to exchange data while protecting sensitive university information.


Section 4: System Features
4.1 Asset Registration
4.1.1 Description and Priority
The Asset Registration feature allows authorized Asset Custodians to register, view, and update campus assets within the system. It maintains essential asset information, including asset name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability. This feature ensures that campus resources are accurately documented and managed throughout their life cycle.
Priority: High (Must Have)
4.1.2 Stimulus/Response Sequences
Register Asset
The Asset Custodian selects the Register Asset option. The system displays the asset registration form. The Asset Custodian enters the required asset information and submits the form. The system validates the entered information and saves the asset record. Upon successful registration, the system displays a confirmation pop-up and sends a confirmation email to the Asset Custodian.
View Registered Asset
The Asset Custodian navigates to the Asset Management section and selects a registered asset. The system retrieves the asset's information and displays its details, including its category, quantity, department, location, condition, estimated value, and availability.
Update Asset Information
The Asset Custodian selects an existing asset and chooses the Edit Asset option. The system displays the current asset information. The Asset Custodian modifies the necessary fields and submits the changes. The system validates and saves the updated information, displays a confirmation pop-up, and sends a confirmation email.
4.1.3 Functional Requirements
FR-2.1: The system shall allow authorized Asset Custodians to register new campus assets.
FR-2.2: The system shall allow Asset Custodians to enter asset information, including name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability.
FR-2.3: The system shall require asset name, description, category, positive whole-number quantity, department, location, condition and availability before registration; missing or invalid mandatory values shall be identified. Purchase date and estimated value may be unavailable, but any supplied date or value shall be validated.
FR-2.4: The system shall store successfully registered asset information and maintain an accessible asset record.
FR-2.5: The system shall allow authorized Asset Custodians to view the information of registered assets under their responsibility.
FR-2.6: The system shall retrieve and display the selected asset's information without modifying its stored data.
FR-2.7: The system shall allow authorized Asset Custodians to update the information of existing registered assets.
FR-2.8: The system shall validate updated asset information before saving changes and shall reject invalid updates while preserving the previously stored information.
FR-2.9: The system shall prevent unauthorized users from registering, viewing, or modifying asset records outside their assigned permissions.
FR-2.10: The system shall display a confirmation pop-up notification after successful asset registration or modification.
FR-2.11: The system shall send a confirmation email to the Asset Custodian's registered email address following successful asset registration or modification.
FR-2.12: The system shall allow the Asset Custodian to cancel asset registration or modification before submission without saving the changes.
FR-2.13: The system shall preserve saved asset records when confirmation email delivery fails, inform the Asset Custodian of the delivery failure, and retain the on-screen success confirmation.
FR-2.14: The system shall preserve the previous asset record if saving a registration or update fails and shall display an appropriate error.
FR-2.15: The system shall assign a unique asset identifier on registration and validate quantity as a positive whole number and estimated value as a nonnegative number.
FR-2.16: The system shall prevent generic asset edits from bypassing required reservation, transfer, maintenance, or life-cycle approvals and shall record the responsible user and timestamp for accepted changes.
FR-2.17: The system shall record the responsible custodian or owner reference and permit authorized upload and viewing of asset photographs and supporting documents, with access restricted to the asset's permitted scope.
4.2 Asset Publication
4.2.1 Description and Priority
The Asset Publication feature allows authorized Asset Custodians to publish, unpublish, and view surplus, idle, or unwanted campus assets. Published assets become visible to other authorized users and departments, allowing them to identify resources available for reuse or transfer. This feature supports efficient resource sharing, reduces unnecessary purchases, and promotes sustainability across the university.
Priority: High (Must Have)
4.2.2 Stimulus/Response Sequences
Publish Asset
The Asset Custodian navigates to the Asset Management section and selects a registered asset. The system displays the asset details and provides the option to publish it. The Asset Custodian confirms publication, and the system updates the asset's publication status to Published. The asset becomes visible to other authorized users, and the Asset Custodian receives a confirmation pop-up and email.
Unpublish Asset
The Asset Custodian selects a previously published asset and chooses the Unpublish Asset option. The system checks whether the asset has any active reservations or pending transfers. If no restrictions exist, the system changes the publication status to Unpublished and removes the asset from available listings. The Asset Custodian receives a confirmation pop-up and email.
View Published Assets
An authorized user navigates to the Available Assets section. The system retrieves and displays published assets that the user has permission to access. The user selects an asset, and the system displays its details, including name, description, category, quantity, department, location, condition, estimated value, and availability.
4.2.3 Functional Requirements
FR-3.1: The system shall allow authorized Asset Custodians to publish registered campus assets that are surplus, idle, or unwanted.
FR-3.2: The system shall allow Asset Custodians to select an existing registered asset for publication.
FR-3.3: The system shall display the selected asset's information and request confirmation before publication.
FR-3.4: The system shall update the asset's publication status to Published following successful publication.
FR-3.5: The system shall make published assets visible to authorized users and departments.
FR-3.6: The system shall allow authorized Asset Custodians to unpublish previously published assets.
FR-3.7: The system shall check for active reservations or pending transfers before allowing an asset to be unpublished.
FR-3.8: The system shall prevent an asset from being unpublished if active reservations or pending transfers exist and shall display an appropriate message.
FR-3.9: The system shall update the asset's publication status to Unpublished and remove it from available asset listings following successful unpublication.
FR-3.10: The system shall allow authorized users to view published assets and their relevant information without modifying stored asset data.
FR-3.11: The system shall display an appropriate message when no published assets are available.
FR-3.12: The system shall prevent unauthorized users from publishing, unpublishing, or accessing restricted asset information.
FR-3.13: The system shall prevent duplicate publication of an asset that is already published.
FR-3.14: The system shall display a confirmation pop-up notification following successful publication or unpublication.
FR-3.15: The system shall send a confirmation email to the Asset Custodian's registered email address following successful publication or unpublication.
FR-3.16: The system shall allow the Asset Custodian to cancel publication or unpublication before confirmation without modifying the asset's publication status.
FR-3.17: The system shall preserve the saved publication status if confirmation email delivery fails and inform the Asset Custodian of the failure.
FR-3.18: The system shall preserve the previous publication status if saving fails and prevent simultaneous repeated operations from creating conflicting publication states.
FR-3.19: The system shall allow publication only when the asset state permits sharing and shall recheck authority and eligibility immediately before saving publication or unpublication.
4.3 AI-Assisted Asset Classification
4.3.1 Description and Priority
The AI-Assisted Asset Classification feature allows authorized Asset Custodians to generate, review, modify, and regenerate AI-based classification recommendations for newly registered campus assets. The AI analyzes asset information, including names, descriptions, and specifications, to recommend suitable categories, tags, and standardized descriptions. This feature improves the consistency and accuracy of asset classification while reducing manual effort. All AI-generated recommendations remain subject to review and acceptance by the Asset Custodian before being applied. The system shall also provide explanations and available confidence information for AI-generated recommendations, allowing Asset Custodians to identify uncertain classifications and make informed decisions.
Priority: Medium (Should Have)
4.3.2 Stimulus/Response Sequences
Generate AI Asset Classification
The Asset Custodian navigates to the Register Asset section and enters the asset's name, description, and relevant specifications. The Asset Custodian selects the Generate AI Classification option. The system sends the information to the AI Classification Service, which analyzes the asset details and generates recommended categories, tags, and a standardized description. The system displays the recommendations for the Asset Custodian to review and accept before applying them to the registration form.
Review and Modify AI Classification Recommendations
The Asset Custodian reviews the AI-generated classification recommendations displayed by the system. The Asset Custodian may accept the recommendations, modify specific fields, or reject them entirely. The system applies the accepted or modified information to the asset registration form. If the recommendations are rejected, the system allows the Asset Custodian to enter the classification information manually.
Regenerate AI Classification Recommendations
The Asset Custodian determines that the initial AI-generated recommendations are unsuitable and modifies or adds asset information. The Asset Custodian selects Regenerate Recommendations. The system sends the updated information to the AI Classification Service, which generates new recommendations. The system displays the updated categories, tags, and descriptions for the Asset Custodian to review before applying them.
4.3.3 Functional Requirements
FR-11.1: The system shall allow authorized Asset Custodians to request AI-generated classification recommendations during asset registration.
FR-11.2: The system shall retrieve the entered asset name, description and specifications, and any authorized photographs or supporting documents supported by the selected AI service, for classification.
FR-11.3: The system shall send the available asset information to the AI Classification Service for analysis.
FR-11.4: The system shall generate recommended asset categories, tags, and standardized descriptions based on the provided asset information.
FR-11.5: The system shall display the AI-generated classification recommendations to the Asset Custodian for review.
FR-11.6: The system shall allow the Asset Custodian to accept AI-generated classification recommendations without modification.
FR-11.7: The system shall allow the Asset Custodian to modify recommended categories, tags, and descriptions before applying them.
FR-11.8: The system shall allow the Asset Custodian to reject AI-generated recommendations and manually enter classification information.
FR-11.9: The system shall apply accepted or modified classification recommendations to the relevant asset registration fields.
FR-11.10: The system shall not automatically save AI-generated classification recommendations to the asset record without confirmation from the Asset Custodian.
FR-11.11: The system shall allow the Asset Custodian to request regeneration of classification recommendations when the initial suggestions are unsuitable.
FR-11.12: The system shall use the most recently provided asset information when regenerating classification recommendations.
FR-11.13: The system shall display the newly generated recommendations without automatically replacing previously accepted asset information.
FR-11.14: The system shall detect insufficient asset information and display a message requesting additional details when suitable recommendations cannot be generated.
FR-11.15: The system shall display an appropriate error message when the AI Classification Service is unavailable or fails to process a request.
FR-11.16: The system shall allow the Asset Custodian to continue asset registration using manual classification when the AI Classification Service is unavailable.
FR-11.17: The system shall validate any modified classification information before applying it to the asset registration form.
FR-11.18: The system shall allow the Asset Custodian to cancel the review or regeneration process without applying unwanted changes to the registration form.
FR-11.19: The system shall display an explanation of the factors used to generate each AI-assisted asset classification recommendation.
FR-11.20: The system shall display an AI confidence score or clearly indicate when confidence information is unavailable.
FR-11.21: The system shall flag low-confidence classification recommendations for manual review and shall not automatically apply them without confirmation from the Asset Custodian.
FR-11.22: The system shall preserve the current registration form and previously accepted information if AI generation or application of suggestions fails and shall allow manual classification.
FR-11.23: The system shall recheck the user's registration permissions before generating, reviewing, regenerating, or applying AI classification suggestions.
FR-11.24: The system shall assess low confidence using the AI service's supplied confidence scale and threshold, display them when available, and flag scores below the threshold; if either is unavailable, the system shall identify confidence assessment as unavailable and require manual review.

Section 5: Other Non-Functional Requirements
This section defines the non-functional requirements of the Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System. These requirements establish measurable standards for system performance, safety, security, reliability, usability, and maintainability. They apply to the overall system and ensure that both traditional asset management functions and AI-enhanced services operate effectively and securely. Disclaimer: The numerical targets defined in this section represent the proposed performance and quality targets for the proposed system. These requirements will be evaluated during testing using documented procedures and measurable results. Any changes to these targets during Agile development shall be formally documented, justified, and reflected in updated requirement specifications.

5.1 Performance Requirements
NFR-1: The system shall return asset search and filtering results within 2 seconds for at least 95% of requests under a workload of 50 concurrent users.
NFR-2: The system shall load the main dashboard and asset management pages within 3 seconds for at least 95% of requests under a workload of 50 concurrent users.
NFR-3: The system shall complete asset registration, modification, and publication operations within 3 seconds for at least 95% of requests under normal operating conditions, excluding email delivery time.
NFR-4: The system shall generate AI-assisted asset classification recommendations within 5 seconds for at least 95% of requests under a workload of 10 concurrent AI requests.
NFR-5: The system shall generate AI-based resource matching recommendations within 5 seconds for at least 95% of requests under a workload of 10 concurrent AI requests.
NFR-6: The system shall support at least 50 concurrent users performing asset searches, registrations, reservations, and request management operations without exceeding the specified response time limits.
5.2 Safety Requirements
NFR-7: The system shall require confirmation from an authorized user before executing irreversible asset management actions, including disposal, retirement, and permanent removal of asset records.
NFR-8: The system shall prevent asset transfers, donations, recycling, and disposal actions from being finalized without the required approvals from authorized personnel.
NFR-9: The system shall maintain a record of critical asset management activities, including approvals, transfers, maintenance, repairs, and disposal decisions, to support accountability and recovery from incorrect actions.
NFR-10: The system shall prevent conflicting asset reservations and transfers from allocating quantities greater than the available asset quantity.
NFR-11: The system shall preserve previously stored asset and transaction information when an operation fails, ensuring that incomplete transactions do not result in inconsistent records.
NFR-12: The system shall prevent AI-generated recommendations from automatically initiating asset disposal, transfer, recycling, or retirement without review and approval by an authorized user.
5.3 Security Requirements
NFR-13: The system shall require users to authenticate using valid login credentials before accessing protected system functions.
NFR-14: The system shall enforce role-based access control to ensure that users can access only the information and functions permitted by their assigned roles.
NFR-15: The system shall protect all data transmitted between users and the application using HTTPS with TLS 1.2 or higher.
NFR-16: The system shall store user passwords using a secure, salted password-hashing algorithm, for example Argon2id, and shall not store passwords in plain text.
NFR-17: The system shall automatically terminate an authenticated session after 15 minutes of inactivity and require the user to authenticate again before accessing protected functions.
NFR-18: The system shall maintain audit logs of security-sensitive activities, including login attempts, permission changes, approval decisions, and modifications to asset records. Each log entry shall include the action, timestamp, and responsible user where applicable.
NFR-19: The system shall prevent unauthorized users from viewing, modifying, deleting, or approving asset records, resource requests, transfers, and maintenance information outside their assigned permissions.
5.4 Software Quality Attributes
NFR-20: Usability
At least 80% of first-time users participating in usability testing shall be able to register an asset or submit a resource request within 3 minutes without external assistance.
NFR-21: Availability
The system shall maintain at least 99% availability during each calendar month, excluding scheduled maintenance periods announced in advance.
NFR-22: Reliability
The system shall maintain data consistency during asset registration, reservations, approvals, and transfers. Failed transactions shall not result in partially saved records or incorrect asset quantities.
NFR-23: Maintainability
The system shall use a modular software architecture that separates user interfaces, business logic, data management, and AI services, allowing individual components to be updated without requiring changes to unrelated modules.
NFR-24: Compatibility
The system shall support the latest stable versions of Google Chrome, Microsoft Edge, and Mozilla Firefox at the time of prototype testing.
NFR-25: Accessibility
The system shall provide keyboard-accessible navigation, clearly labeled form controls, and readable error messages. 
NFR-26: AI Reliability
When an AI service is unavailable or fails to generate recommendations, the system shall display an appropriate error message and allow users to continue applicable operations using manual classification, conventional search, or rule-based alternatives.
NFR-27: Data Integrity
The system shall ensure that each registered asset has a unique identifier and that updates to asset ownership, location, condition, and life-cycle status are recorded without overwriting historical events.
NFR-28: Testability
The system shall support testing of its main functional modules, including asset registration, resource requests, reservations, approvals, transfers, maintenance, and AI recommendations, using documented test cases with defined expected results.
5.5 Business Rules
BR-1: Only authenticated users with appropriate permissions shall be allowed to access protected system functions.
BR-2: Asset Custodians shall only register, publish, modify, and manage assets within their assigned authority.
BR-3: Only registered assets shall be eligible for publication, reservation, or transfer.
BR-4: Resource requests shall include valid information such as resource category, specifications, quantity, urgency, location, and required date.
BR-5: Users shall not be permitted to approve their own resource requests.
BR-6: Asset reservations shall only be created after the required approval has been granted.
BR-7: The total reserved quantity of an asset shall not exceed its available quantity.
BR-8: Asset transfers shall require authorization before dispatch and confirmation of receipt before completion.
BR-9: Asset custody and location records shall only be updated after the receiving department confirms the transfer.
BR-10: Maintenance and repair activities shall be recorded in the asset's life-cycle history.
BR-11: Donation, recycling, retirement, and disposal actions shall require approval from authorized personnel before implementation.
BR-12: AI-generated classifications, resource matches, and sustainability recommendations shall remain advisory. Final decisions shall be made by authorized users.
BR-13: When multiple departments request the same asset, the system shall provide decision-support information such as urgency, required date, suitability, availability, and sustainability impact. The final allocation decision shall remain with an authorized approver.
BR-14: Cancelled, rejected, and completed requests and transfers shall remain accessible to authorized users for historical review and auditing.
BR-15: Financial savings and environmental impact estimates shall be calculated using documented assumptions and available operational data.
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
Appendix B: Analysis Models
This appendix presents the overall UML use case diagram for the Circular Campus Resource Exchange and Asset Life Cycle Management System. The diagram illustrates the primary system actors, their interactions with major system functionalities, and the relationships between use cases. It provides a high-level representation of the system's expected behavior and supports the detailed use case descriptions presented in Section 7.
B1 Overall Use Case Diagram
The same Authorized Campus User actor is repeated across the three columns to keep the diagram readable. Each association is subject to the role and department permissions in Section 2.3 and FR-1. Individual feature diagrams in Section 7 identify the specific staff and external-service actors. No AI service can override an approval or receipt workflow.
 
Figure B1 Overall use case overview of all 15 system features
B2 Feature and Requirement Traceability
Feature	Requirement Range	Use Cases
4.1 Asset Registration	FR-2.1 to FR-2.17	7.1.1, 7.1.2, 7.1.3
4.2 Asset Publication	FR-3.1 to FR-3.19	7.2.1, 7.2.2, 7.2.3
4.3 AI Assisted Asset Classification	FR-11.1 to FR-11.24	7.3.1, 7.3.2, 7.3.3
4.4 Asset Search and Filtering	FR-4.1 to FR-4.17	7.4.1, 7.4.2, 7.4.3
4.5 Resource Requests	FR-5.1 to FR-5.23	7.5.1, 7.5.2, 7.5.3, 7.5.4
4.6 Reservation Management	FR-6.1 to FR-6.20	7.6.1, 7.6.2, 7.6.3
4.7 Approval Management	FR-7.1 to FR-7.18	7.7.1, 7.7.2, 7.7.3
4.8 Transfer Management	FR-8.1 to FR-8.21	7.8.1, 7.8.2, 7.8.3, 7.8.4
4.9 Asset Life Cycle Tracking	FR-9.1 to FR-9.22	7.9.1, 7.9.2, 7.9.3, 7.9.4
4.10 Maintenance and Repair Tracking	FR-10.1 to FR-10.20	7.10.1, 7.10.2, 7.10.3, 7.10.4
4.11 Sustainability Recommendations	FR-13.1 to FR-13.20	7.11.1, 7.11.2, 7.11.3
4.12 AI Based Resource Matching	FR-12.1 to FR-12.20	7.12.1, 7.12.2, 7.12.3
4.13 Reporting	FR-15.1 to FR-15.17	7.13.1, 7.13.2, 7.13.3
4.14 Authentication and Access Control	FR-1.1 to FR-1.17	7.14.1, 7.14.2, 7.14.3, 7.14.4
4.15 LLM Powered Assistant	FR-14.1 to FR-14.16	7.15.1, 7.15.2, 7.15.3
Appendix C: To Be Determined (TBD) List
This appendix identifies requirements and implementation details that have not yet been finalized. These items will be reviewed and resolved during the subsequent design and development phases, with any resulting changes documented in updated versions of the SRS.
TBD-01: Select the AI services and document their available confidence scales and thresholds during design. Until comparable confidence information exists, the manual-review fallback in FR-11.24 applies.
TBD-02: Confirm optional asset metadata and permitted vocabularies with the team. Mandatory registration fields and numeric validation are specified in FR-2 and shall not remain undefined at implementation.
TBD-03: The specific AI services or models used for asset classification, resource matching, and sustainability recommendations will be selected during system design.
TBD-04: The final hosting environment and database technologies will be determined during the architecture design phase.
TBD-05: The availability of historical procurement records and environmental data required for sustainability calculations will be confirmed before system evaluation.
