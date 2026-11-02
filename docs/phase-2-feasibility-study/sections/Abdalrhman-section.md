7.0 Legal and Regulatory Analysis Circular Campus Resource Exchange and Asset Life Cycle Management System

7.1 Purpose and assessment                         

For our Circular Campus project, we need to consider how we handle user information, use external software, and manage university assets. These issues are part of the Phase 2 feasibility study . We recommend starting with fictional data and simulated transfers. This follows our Phase 1 plan to control user access and keep approval decisions with authorized people .

7.2 Data protection and confidentiality 

Our system may store names, university emails, requests, and asset records. We should collect only the information needed and use fictional records while developing the prototype. One relevant law is Federal Decree-Law No. 45 of 2021. However, Article 2 excludes government data and governmental entities that control or process personal data, among other categories . We therefore need to confirm which rules apply to KU and the service providers we choose. Before using real data, we should clarify who can access it, how long it can be kept, and how it can be corrected or deleted. Storing or sharing data outside the UAE also needs review .

7.3 Security and access control                

Each user should only access the records and functions allowed by their role. For example, a requester should not approve their own request . We should protect login details, use encrypted connections, and record important changes and approvals. Passwords, API keys, and confidential records should stay out of GitHub. We also need to confirm KU’s rules for hosting, backups, and reporting security incidents.


7.4 Software licensing and intellectual property Our project may use code libraries, images, datasets, and AI services created by others.

We should check their licenses and include any required credits or notices. The UAE copyright framework includes Federal Decree-Law No. 38 of 2021 . Finding something online does not automatically give us permission to reuse it. We should also review copied or AI-assisted code and confirm the course and KU rules on ownership and publishing our work.
7.5 Asset ownership and approvals 

Before a real transfer, the responsible university staff should check who owns the item and whether its purchase, lease, or funding terms restrict its use. Moving a KU-owned item between departments may change its location and custodian while KU remains the owner. Our system should record the approval and handover. The exact approval roles and financial limits still need confirmation. KU’s compliance portal provides guidance on university policies .


 
7.6 AI services and human accountability    

AI may suggest an unsuitable item or action, so an authorized person should review its recommendations. The assistant should follow the same access rules as the rest of the system and should not approve transfers or disposal by itself . We should check how an AI provider stores data, uses it for training, and handles deletion before choosing it. Real personal or confidential information should only be used when authorized. The system should explain recommendations and clearly label estimated savings and environmental benefits.

7.7 Equipment safety and waste disposal                   

We should record equipment inspections and stop unsafe items from being transferred until responsible staff clear them. Hazardous or specialist items need an approved Environment, Health and Safety process. KU’s Waste Management Procedure says non-medical electronic waste must go through Facilities Management collection rather than general waste. IT equipment must first go to the IT Department for decommissioning to protect its data. The procedure also requires approved licensed contractors and disposal records . Our system should record these steps. We still need to confirm the inspection and data removal rules for equipment being reused.
7.8 Contribution to the final recommendation Based on this analysis, we recommend continuing with a student prototype using fictional data and simulated transfers. Before testing it with real university records or assets, we need to confirm the privacy, hosting, approval, licensing, and safety requirements with the relevant KU staff. We also need to implement and test the proposed controls. Our group should consider these conditions alongside the technical, financial, operational, and schedule findings when making the final feasibility decision.


















8 Risk Assessment

8.1 Purpose and rating method

Risk assessment identifies events that could prevent the team from completing a useful, secure, and testable prototype. Each risk is rated using qualitative probability and impact levels:
Low: Unlikely to occur or expected to cause limited disruption.
Medium: Could occur and may require changes to the plan.
High: Likely to occur or capable of threatening a major deliverable.
The team should review the risk register weekly. A risk owner monitors each item, reports changes, and coordinates the response. Ownership does not mean that one person handles the risk alone.

8.2 Risk register
ID
Risk
Probability
Impact
Prevention and mitigation
Contingency if it occurs
Owner
R1
The project scope is too large for one semester
High
High
Complete must-have functions before should-have and could-have functions; review scope weekly
Remove or simplify optional AI, reporting, and convenience features while preserving the core workflow
Ahmad
R2
Requirements or approval rules remain unclear
Medium
High
Confirm workflows with instructors and available stakeholders during Phase 3; document assumptions
Implement configurable prototype rules and clearly label unconfirmed decisions in the documentation
Ahmad
R3
A course milestone is missed
Medium
High
Break work into weekly tasks, assign owners, and monitor progress
Reassign work, reduce optional scope, and agree on a recovery plan before the next milestone
Ahmad and all members
R4
Team workload becomes uneven or a member is unavailable
Medium
Medium
Keep tasks visible in GitHub and review workload weekly
Transfer urgent tasks to another member and document the reassignment
Ahmad and all members
R5
The team lacks experience with a selected technology
Medium
High
Select familiar technologies where possible and build an early technical prototype
Replace the difficult component with a simpler supported alternative
Abdulrahman
R6
Frontend, backend, database, and AI components fail to integrate
Medium
High
Define interfaces early and integrate small increments throughout development
Disable the failing optional component, preserve the core workflow, and demonstrate it separately if necessary
Abdulrahman and Abdullah
R7
Suitable university data is unavailable
Medium
High
Request only authorized information and design realistic test data early
Use documented synthetic data and state that results are illustrative
Ahmad and Khalid
R8
Sensitive data, credentials, or access permissions are mishandled
Medium
High
Use test data, role-based permissions, secure configuration, and a .gitignore; never commit secrets
Revoke exposed credentials immediately, remove access, inform the team and instructor, and replace the affected data or service
Abdulrahman
R9
AI produces inaccurate, biased, or unsuitable recommendations
High
High
Use AI only for suggestions, provide explanations, test representative cases, and require human review
Allow authorized users to reject the output and use rule-based or manual decisions when confidence is insufficient
Khalid
R10
AI or cloud services become unavailable or too expensive
Medium
Medium
Monitor free-tier limits and isolate external services behind replaceable interfaces
Use a lower-cost service, local mock responses, or a non-AI fallback for the demonstration
Khalid
R11
Users find the workflows confusing or do not trust the system
Medium
Medium
Review interface designs early and test common workflows with representative users when possible
Simplify screens, improve instructions, and provide manual alternatives for AI-assisted actions
Abdullah
R12
Testing begins too late to correct major defects
Medium
High
Prepare test cases during development and test each increment
Freeze optional features and focus the remaining time on integration and critical defects
Abdullah and all members
R13
Team members overwrite work or create Git conflicts
Medium
Medium
Use separate files and branches, pull current changes, and review pull requests before merging
Resolve conflicts using the last reviewed version and recover earlier work from Git history
All members
R14
Financial or sustainability estimates cannot be supported
Medium
Medium
Record data sources, formulas, units, and assumptions; request stakeholder review
Present scenario ranges instead of unsupported exact values and identify the data needed for a real deployment
Khalid
R15
Legal, privacy, licensing, or university-policy requirements restrict the proposed approach
Medium
High
Use authorized data and approved tools; review software licenses and relevant university requirements
Remove restricted data or services, replace them with test data or approved alternatives, and revise the affected feature
Khalid and Ahmad

8.3 Highest-priority risks

The team should give immediate attention to scope growth, unclear requirements, schedule delay, system integration, data availability, security, and unreliable AI recommendations. These risks can directly prevent completion or make the prototype unsuitable for demonstration. The primary response is to protect the must-have workflow, validate assumptions early, integrate continuously, and keep all AI decisions subject to authorized human review.

8.4 Risk monitoring process

At the weekly progress review, the team should:
Check whether the probability or impact of any existing risk has changed.
Record newly identified risks.
Confirm whether preventive actions were completed.
Assign an owner and deadline for each required response.
Decide whether scope, schedule, or responsibilities need adjustment.
Record the decision in the project documentation or GitHub issue history.

8.5 Risk feasibility finding

The identified risks are significant but manageable for an academic prototype. No listed risk currently requires the team to stop the project. Feasibility depends on limiting the scope, using authorized or synthetic data, testing integrations early, protecting sensitive information, and maintaining human oversight of AI recommendations. If these controls cannot be maintained, the team should reduce the affected feature or reconsider that part of the proposed system.

