## 1 Project Scope

### 1.1 Project problem

Universities manage many resources, including computers, laboratory equipment, furniture, books, and office materials. A department may need an item while a similar usable item remains idle in another department. Without a shared system, staff may not know which resources are available, how to request them, who must approve a transfer, or how ownership and location records should be updated. This can lead to unnecessary purchases, wasted resources, and incomplete asset histories.

The Circular Campus project addresses this problem through an internal university platform for sharing resources and managing their life cycles. Departments will be able to publish available assets, search for resources, submit requests, obtain approval, arrange transfers, and maintain records about condition, ownership, location, maintenance, and end-of-life actions. The platform will also provide AI assistance while keeping final decisions under human control.

### 1.2 Project goal

The goal is to develop a working academic prototype that demonstrates how a university could improve resource reuse and asset management. The prototype should make the movement and condition of assets easier to track, reduce unnecessary purchases and waste, and provide understandable estimates of financial and environmental benefits.

### 1.3 Project objectives

The project has the following objectives:

- Help departments identify and reuse available campus resources.
- Reduce unnecessary purchases and the disposal of usable assets.
- Organize resource requests, reservations, approvals, and transfers.
- Maintain accurate records of asset ownership, custody, location, condition, and maintenance.
- Extend the useful life of assets through reuse, repair, and refurbishment.
- Provide AI suggestions with understandable explanations.
- Support authorized decision makers without replacing their authority.
- Track reuse and repair activity and estimate financial and environmental benefits using stated assumptions.

### 1.4 Intended deliverable

The project will deliver a working prototype for internal campus resource exchange and asset life-cycle management. The prototype should demonstrate the complete core workflow: an authorized user registers or publishes an asset, another user finds it and submits a request, an authorized person reviews the request, the transfer is recorded, and the asset's ownership, custody, location, condition, and history are updated.

The prototype should also demonstrate selected AI-assisted functions if the core workflow is stable and enough time remains. AI outputs will be recommendations rather than automatic decisions.

### 1.5 Functional scope

The scope is organized using the MoSCoW priorities established in Phase 1.

#### Must have

- User authentication and role-based access control
- Asset registration and maintenance of asset records
- Publication of surplus, idle, or unwanted resources
- Search and filtering of available assets
- Resource requests and reservations
- Approval and transfer management
- Tracking of ownership, custody, and location changes
- Asset life-cycle tracking, including maintenance, repair, transfer, refurbishment, donation, recycling, retirement, and disposal
- Basic operational reporting

These functions form the minimum viable prototype. The team should complete and test them before depending on advanced AI features.

#### Should have

- AI matching between departmental requests and available assets
- AI-assisted asset classification and tagging
- Sustainability recommendations for reuse, repair, refurbishment, recycling, or retirement
- Notifications about requests, approvals, transfers, and asset status

These features add value but depend on reliable core data and workflows.

#### Could have

- A natural-language assistant for searching, requesting resources, and navigating the platform
- Generative AI summaries and reports
- More detailed recommendation explanations
- Additional sustainability insights and convenience features

The team may reduce or postpone these features if they threaten completion of the core system.

### 1.6 Scope boundaries

For the feasibility study, the project is treated as an academic prototype rather than a production deployment across Khalifa University. The following boundaries are proposed:

- The prototype will use test data or information that the team is authorized to use.
- It will not connect to official university asset databases unless the university provides permission and technical access.
- It will not replace official financial, procurement, maintenance, or asset-management systems.
- It will not automatically approve requests or decide whether an asset should be transferred, donated, recycled, or disposed of.
- Authorized users will review, accept, or reject AI recommendations.
- A full production rollout, integration with existing university systems, long-term support, and institutional policy changes fall outside the current semester.

These boundaries should be confirmed with the instructors and refined during the detailed requirements phase.

### 1.7 Scope constraints and assumptions

The preliminary feasibility decision depends on several constraints:

- The project budget has not yet been confirmed.
- Development must follow the course deadlines.
- Progress depends on the team's available time, technical skills, computers, and access to suitable tools.
- Suitable real university data may not be available, so realistic test data may be required.
- AI recommendations may be incomplete or incorrect and must remain subject to human review.
- Approval authorities and financial limits still need confirmation from relevant stakeholders.

The project scope appears feasible only if the team prioritizes the minimum viable prototype and treats advanced AI functions as later increments.

## 2 Stakeholder Analysis

### 2.1 Purpose of the stakeholder analysis

The system affects people who request resources, manage assets, authorize transfers, maintain equipment, administer the platform, and evaluate financial and environmental outcomes. Identifying these stakeholders helps the team determine the required features, data, permissions, approval responsibilities, and reporting needs. It also reveals whether the system can operate realistically within a university.

### 2.2 Stakeholders responsibilities and expectations

| Stakeholder | Main involvement | Needs and expectations | Feasibility concern to confirm |
|---|---|---|---|
| Requesters and department representatives | Identify needs, search for resources, submit requests, and confirm receipt | Accurate listings, useful search filters, fair allocation, explanations, and status updates | Whether the request process fits current departmental practices |
| Asset custodians | Register and publish assets, maintain records, verify condition, and coordinate handovers | Clear ownership, accurate location and condition, supporting documents, and complete asset history | Who may publish or modify an asset record |
| Approvers and asset administrators | Review requests and authorize transfers and end-of-life actions | Clear approval rules, decision-support information, costs, reasons, and audit records | Exact approval authority and financial limits |
| Maintenance staff | Inspect assets, report defects, record repairs, and update condition | Technical information, inspection records, service history, repair costs, and maintenance status | How maintenance information will be verified and updated |
| Procurement and finance officers | Review purchase alternatives, values, costs, and savings | Reliable financial data and evidence supporting avoided-purchase estimates | Which cost assumptions and savings calculations they will accept |
| Sustainability officers | Review reuse, repair, recycling, waste diversion, and environmental estimates | Transparent methods, traceable data, and clearly stated assumptions | Which environmental measures and calculation methods are authorized |
| System administrators | Manage accounts, roles, permissions, configuration, security, and logs | Secure access, reliable operation, backups, and system activity records | Hosting, authentication, security, and support requirements |
| University management | Review performance and guide policy | Useful operational, financial, and sustainability reports | Which indicators are useful for management decisions |
| Project team | Gather requirements, design, develop, test, and document the prototype | Clear responsibilities, access to tools, stakeholder feedback, and coordinated work | Whether the team has enough time and technical capability |
| Instructors and lab staff | Guide the team and assess deliverables | Complete documentation, a working prototype, and visible individual contributions | Submission expectations and assessment criteria for each phase |

### 2.3 Access and approval boundaries

Access should depend on each user's role. Requesters may submit and track requests but should not approve their own requests. Asset custodians may maintain records for assigned assets and confirm approved handovers. Approvers may approve or reject actions within their assigned authority. Maintenance staff may update inspection, repair, and condition records. System administrators may manage technical access and configuration.

The system should separate requesting, reviewing, approving, handing over, and confirming receipt. After a transfer is approved, the source custodian and receiving user should confirm the handover so the system can update ownership, custody, and location records.

When several departments request the same asset, the system may present information about urgency, required date, purpose, suitability, quantity, transfer or repair cost, and sustainability benefit. AI may rank options, but an authorized stakeholder must make and record the final decision.

### 2.4 Stakeholder involvement plan

The team should confirm stakeholder requirements through the following activities:

1. Review the provided project brief and the Phase 1 requirements.
2. Interview or obtain feedback from potential requesters, department representatives, asset custodians, approvers, maintenance staff, and administrators when access is possible.
3. Use a short structured questionnaire to compare stakeholder priorities, such as search filters, availability information, request tracking, approval information, and notifications.
4. Ask finance, procurement, and sustainability stakeholders to review the proposed cost and environmental calculations.
5. Ask system administrators to confirm access-control, security, data, and hosting expectations.
6. Show stakeholders an early prototype or workflow and record requested changes.

Questions should include:

- How do departments currently discover resources available elsewhere?
- What information does an approver need before accepting a transfer?
- When does responsibility for an asset move to the receiving department?
- What explanation would make an AI recommendation understandable and trustworthy?
- Which information may be stored in the prototype, and which information requires authorization?

### 2.5 Stakeholder feasibility finding

The project has identifiable users and a clear reason for each stakeholder to participate. This supports operational feasibility. However, the team has not yet confirmed every approval rule, data-access restriction, reporting method, or stakeholder expectation. The project can proceed as a prototype using test or authorized data, provided that unresolved authority and policy questions are recorded and refined during the requirements phase.

## 3 Project Schedule

### 3.1 Course milestones

The project will follow an Agile approach and progress incrementally through the course phases.

| Phase | Main activity and deliverable | Scheduled period | Duration stated in course slides |
|---|---|---|---|
| Phase 1 | Initial plan and requirement gathering document | Labs in the week of September 14, 2026 | 1 week |
| Phase 2 | Feasibility document | Labs in the week of September 21, 2026 | 1 week |
| Phase 3 | Detailed requirements document | Labs in the week of October 5, 2026 | 2 weeks |
| Phases 4 and 5 | Architecture and detailed design document | Labs in the week of October 26, 2026 | 3 weeks |
| Phase 6 | Draft implementation with major features | Labs in the week of November 16, 2026 | 3 weeks |
| Phase 7 | Test-case details and testing preparation | Labs in the week of November 23, 2026 | 1 week |
| Phase 8 | Final project, presentation, and demonstration | The course slide places it in the week of November 23, 2026 | Exact final date and duration should be confirmed |

### 3.2 Development sequence

The proposed development sequence is:

1. Complete the feasibility decision and identify conditions for proceeding.
2. Confirm detailed functional and non-functional requirements.
3. Select the architecture, technologies, database design, and AI integration approach.
4. Implement authentication and role-based permissions.
5. Implement asset registration, publication, search, and filtering.
6. Implement requests, reservations, approvals, transfers, and confirmation of receipt.
7. Implement maintenance records, life-cycle history, and basic reporting.
8. Add selected AI classification, matching, or sustainability functions.
9. Integrate the components and execute the test cases.
10. Correct defects and prepare the final demonstration, documentation, and presentation.

This sequence keeps the minimum viable workflow ahead of optional features.

### 3.3 Team coordination

The team will review progress weekly and may reassign tasks when a member is blocked or when one area requires additional work. Each member will record meaningful contributions using their own GitHub account. Documentation and implementation changes should use clear commit messages, separate branches, and pull requests when review is needed.

The Phase 1 roles provide the initial allocation of responsibility:

- Ahmad Salim coordinates tasks, tracks deadlines, and maintains requirements and documentation.
- Abdullah Shehada works on interface design and development and supports testing and quality review.
- Abdulrahman works on system and database development.
- Khalid works on AI functions, sustainability recommendations, and related reporting.

All members will review documents, test the system, and prepare the final presentation.

### 3.4 Schedule dependencies

The schedule contains several important dependencies:

- Architecture and design depend on stable requirements.
- Implementation depends on agreed technologies, database design, and interfaces.
- AI functions depend on usable asset and request data from the core system.
- Reporting depends on reliable records of requests, transfers, maintenance, costs, and outcomes.
- System testing depends on integrated and sufficiently stable features.
- The final demonstration depends on completing integration and correcting major defects early enough.

Delays in requirements, technology selection, data preparation, or integration could affect every later phase.

### 3.5 Schedule risks and responses

| Schedule risk | Possible effect | Planned response |
|---|---|---|
| Scope is too large for one semester | Core features or testing may remain incomplete | Complete must-have functions first and postpone could-have features |
| Team needs time to learn selected technologies | Implementation begins late or contains defects | Select technologies early and build a small technical prototype before full development |
| Requirements change after development starts | Rework and delays | Review requirements regularly and record changes through the Agile process |
| AI integration takes longer than expected | Core system delivery is threatened | Isolate AI features and demonstrate one limited use case after the core workflow works |
| Test data is unavailable | AI and reporting features cannot be validated | Prepare realistic authorized test data and document its assumptions |
| Integration happens too late | Components fail near the final deadline | Integrate in small increments and test throughout development |
| Work is unevenly distributed | Some sections or components fall behind | Review workload weekly and reassign tasks when needed |

The main risk owner should include these items in the group's combined risk assessment.

### 3.6 Schedule feasibility finding

The course schedule is demanding but feasible for an academic prototype if the team controls scope, completes requirements and design before major implementation, integrates features incrementally, and protects adequate time for testing. Completing every proposed AI feature would increase schedule risk. The team should therefore treat the core asset-management workflow as the required result and introduce AI capabilities in priority order.

## 4 Conclusion for Assigned Areas

The project has a clear problem, defined users, and a workable minimum scope. Its stakeholders have identifiable responsibilities and information needs, although approval rules, access restrictions, and reporting assumptions still require confirmation. The schedule can support a working prototype if the team uses the MoSCoW priorities, reviews progress weekly, and postpones optional AI functions when they threaten the core deliverable.

Based on the scope, stakeholder, and schedule analysis, these three areas support proceeding with the project under the following conditions:

- The team must complete the must-have asset-management workflow before advanced AI features.
- The prototype must use test or authorized data.
- Authorized users must retain responsibility for approvals and final decisions.
- The team must confirm unresolved stakeholder permissions and approval rules during Phase 3.
- Progress, workload, risks, and scope must be reviewed every week.
- The exact Phase 8 deadline and submission method should be confirmed with the instructors.

## References

1. Group 4. *Intelligent AI Powered Circular Campus Resource Exchange and Asset Life Cycle Management System Phase 1 Initial Plan and Requirement Gathering Document*. COSC 336, Khalifa University, Fall 2026.
2. COSC 336 teaching team. *Phase 2 Feasibility Study*. Khalifa University, Fall 2026.
