 
Introduction:
This report presents the use case diagrams and detailed use case descriptions for the Intelligent, AI-Powered Circular Campus Resource Exchange and Asset Life Cycle Management System. The purpose of this report is to illustrate how different actors interact with the system and how its functional requirements are fulfilled.
Each system feature is represented through UML use case diagrams and supported by detailed descriptions outlining the actors, goals, preconditions, postconditions, main success scenarios, and alternative flows. These models provide a clear understanding of the system's expected behavior and serve as a foundation for the upcoming design and development phases.
Work split:
System features 1,2,3: Abdullah Shehada
System features 4,5,12: Khaled Sandoqa
System features 6,7,8: Abdalrhman Shihoub 
System features 9,10,11: Ahmad Salim

System Feature 1
 
 Use case diagram 1
1.1: Register Asset
Use Case ID: UC-01
Use Case Name: Register Asset
Related Requirement: FR-2: Asset Registration
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to register a new campus asset in the system.
Preconditions: The Asset Custodian is logged in and has permission to register assets.
Postconditions: The new asset is successfully registered, and its information is stored in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been registered successfully.


1.	The Asset Custodian selects the Register Asset option.
2.	The system displays the asset registration form.
3.	The Asset Custodian enters the asset name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability.
4.	The Asset Custodian submits the registration form.
5.	The system validates the entered information.
6.	The system saves the asset information.
7.	The system displays a confirmation pop-up indicating successful asset registration.
8.	The system sends a confirmation email to the Asset Custodian's registered email address.

Alternative Flows:
A1: Missing or Invalid Information (Exception flow)
At step 5, the system detects missing or invalid information.
The system displays an error message identifying the issue.
The Asset Custodian corrects the information and resubmits the form.
A2: Registration Cancelled
Before submitting, the Asset Custodian cancels the registration.
The system returns to the previous page without saving the asset.

1.2: View Registered Asset
Use Case ID: UC-02
Use Case Name: View Registered Asset
Related Requirement: FR-2: Asset Registration
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to view the details of an asset registered in the system.
Preconditions: The Asset Custodian is logged in, has permission to view the asset, and the asset is already registered in the system.
Postconditions: The system displays the selected asset's information without modifying its stored data.
Main Success Scenario
1.	The Asset Custodian logs into the system.
2.	The Asset Custodian navigates to the Asset Management section.
3.	The system displays a list of registered assets that the custodian is authorized to access.
4.	The Asset Custodian selects an asset from the list.
5.	The system retrieves the selected asset's information.
6.	The system displays the asset's name, description, category, quantity, department, location, condition, purchase date, estimated value, and availability.
Alternative Flows
A1: No Registered Assets
At step 3, the system finds no registered assets accessible to the Asset Custodian.
The system displays a message indicating that no assets are available.
A2: Asset Not Found (Exception Flow)
At step 5, the selected asset no longer exists or cannot be retrieved.
The system displays an error message and allows the Asset Custodian to return to the asset list.
A3: Unauthorized Access (Exception flow)
At step 5, the Asset Custodian does not have permission to view the selected asset.
The system denies access and displays an appropriate error message.

1.3: Update Asset Information
Use Case ID: UC-03
Use Case Name: Update Asset Information
Related Requirement: FR-2: Asset Registration
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to update the information of an existing registered asset to ensure that its details remain accurate and up to date.
Preconditions: The Asset Custodian is logged in, has permission to modify the selected asset, and the asset is already registered in the system.
Postconditions: The updated asset information is successfully saved in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset information has been updated successfully.
Main Success Scenario
1.	The Asset Custodian navigates to the Asset Management section.
2.	The system displays a list of registered assets.
3.	The Asset Custodian selects an asset and clicks Edit Asset.
4.	The system displays the asset's current information.
5.	The Asset Custodian modifies the required fields.
6.	The Asset Custodian submits the updated information.
7.	The system validates and saves the changes.
8.	The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1: Invalid Information: The system displays an error message and asks the Asset Custodian to correct the information.
A2: Update Cancelled: The Asset Custodian cancels the update, and the system keeps the original asset information unchanged.
A3: Unauthorized Update: The system denies the update if the Asset Custodian does not have the required permissions.

System Feature 2
 
Use case diagram 2
2.1: Publish Asset
Use Case ID: UC-04
Use Case Name: Publish Asset
Related Requirement: FR-3: Asset Publication
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to publish surplus, idle, or unwanted campus assets so that other authorized users and departments can view and request them.
Preconditions: The Asset Custodian is logged in, has permission to publish assets, and the asset is already registered in the system.
Postconditions: The selected asset is successfully published and becomes visible to other authorized users and departments. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been published successfully.
Main Success Scenario
1.	The Asset Custodian navigates to the Asset Management section.
2.	The system displays the registered assets.
3.	The Asset Custodian selects an asset to publish.
4.	The Asset Custodian clicks Publish Asset.
5.	The system displays the asset details and asks for confirmation.
6.	The Asset Custodian confirms publication.
7.	The system updates the asset's publication status to Published.
8.	The asset becomes visible to other authorized users.
9.	The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1: Asset Already Published: The system informs the Asset Custodian that the asset is already published.
A2: Publication Cancelled: The Asset Custodian cancels the process, and the asset remains unpublished.
A3: Unauthorized Publication: The system denies publication if the user does not have the required permissions. (Exception flow)

2.2: Unpublish Asset
Use Case ID: UC-05
Use Case Name: Unpublish Asset
Related Requirement: FR-3: Asset Publication
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to remove a previously published asset from public listings when it is no longer available for sharing or transfer.
Preconditions: The Asset Custodian is logged in, has permission to manage the selected asset, and the asset is already published in the system.
Postconditions: The selected asset is successfully unpublished and is no longer visible in the available asset listings to other departments. The asset's information remains stored in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been unpublished successfully.
UC-05: Unpublish Asset
Use Case ID: UC-05
Use Case Name: Unpublish Asset
Related Requirement: FR-3: Asset Publication
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to remove a previously published asset from public listings when it is no longer available for sharing or transfer.
Preconditions: The Asset Custodian is logged in, has permission to manage the selected asset, and the asset is already published in the system.
Postconditions: The selected asset is successfully unpublished and is no longer visible in the available asset listings to other departments. The asset's information remains stored in the system. The Asset Custodian receives a confirmation pop-up notification and an email confirming that the asset has been unpublished successfully.
Main Success Scenario
1.	The Asset Custodian navigates to the Asset Management section.
2.	The system displays the registered assets.
3.	The Asset Custodian selects a published asset.
4.	The Asset Custodian clicks Unpublish Asset.
5.	The system displays a confirmation message.
6.	The Asset Custodian confirms the action.
7.	The system checks whether the asset has any active reservations or pending transfers.
8.	If no restrictions exist, the system changes the asset's publication status to Unpublished.
9.	The asset is removed from the available asset listings.
10.	The system displays a confirmation pop-up and sends a confirmation email.
Alternative Flows
A1: Asset Already Unpublished: The system informs the Asset Custodian that the selected asset is not currently published.
A2: Active Reservations or Pending Transfers: The system prevents unpublishing the asset and informs the Asset Custodian that existing requests or transfers must be resolved first.
A3: Unpublishing Cancelled: The Asset Custodian cancels the operation, and the asset remains published.
A4: Unauthorized Action: The system denies the operation if the Asset Custodian lacks the required permissions. (Exception flow)
2.3: View Published Assets
Use Case ID: UC-06
Use Case Name: View Published Assets
Related Requirement: FR-3: Asset Publication
Primary Actor: Authorized User (Department Representative or Asset Custodian)
Goal: Allow authorized users to view assets published by different university departments to identify resources available for reuse or transfer.
Preconditions: The user is logged into the system and has permission to view published assets. At least one asset has been published in the system.
Postconditions: The system displays the published assets and their relevant information without modifying any stored asset data.
Main Success Scenario
1.	The user logs into the system.
2.	The user navigates to the Available Assets section.
3.	The system retrieves all published assets that the user is authorized to view.
4.	The system displays a list of published assets.
5.	The user selects an asset from the list.
6.	The system displays the asset's name, description, category, quantity, department, location, condition, estimated value, and availability.
7.	The user reviews the asset information.
Alternative Flows
A1: No Published Assets
At step 3, the system finds no published assets.
The system displays a message indicating that no assets are currently available.
A2: Asset No Longer Available
At step 5, the selected asset has been unpublished or is no longer available.
The system informs the user that the asset is unavailable and returns to the asset listings.
A3: Unauthorized Access (Exception flow)
The user attempts to view an asset they do not have permission to access.
The system denies access and displays an appropriate error message.
System Feature 3
 
					Use case diagram 3
3.1: Generate AI Asset Classification
Use Case ID: UC-07
Use Case Name: Generate AI Asset Classification
Related Requirement: FR-11: AI-Assisted Asset Classification
Primary Actor: Asset Custodian
Supporting Actor: AI Classification Service
Goal: Allow the Asset Custodian to use AI to automatically generate recommended categories, tags, and standardized descriptions for newly registered campus assets, reducing manual effort and improving classification accuracy.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The Asset Custodian has entered the necessary asset information, such as the asset name, description, and specifications.
Postconditions: The AI generates recommended categories, tags, and a standardized description for the asset. The recommendations are displayed to the Asset Custodian for review and are not applied until the Asset Custodian accepts them.
Main Success Scenario
1.	The Asset Custodian navigates to the Register Asset section.
2.	The Asset Custodian enters the asset's name, description, and relevant specifications.
3.	The Asset Custodian clicks Generate AI Classification.
4.	The system sends the entered asset information to the AI Classification Service.
5.	The AI analyzes the provided information and generates a recommended category, tags, and standardized description.
6.	The system displays the AI-generated recommendations to the Asset Custodian.
7.	The Asset Custodian reviews the recommendations.
8.	The Asset Custodian accepts the recommendations.
9.	The system fills the relevant registration fields with the accepted recommendations.
10.	The Asset Custodian can continue with the asset registration process.
Alternative Flows
A1: Insufficient Asset Information
At step 5, the AI cannot generate suitable recommendations because the provided information is insufficient.
The system asks the Asset Custodian to provide additional asset details.
A2: AI Service Unavailable (Exception flow)
At step 4, the AI Classification Service is unavailable.
The system displays an error message and allows the Asset Custodian to classify the asset manually.
A3: Recommendations Rejected
At step 7, the Asset Custodian rejects the AI-generated recommendations.
The system allows the Asset Custodian to manually enter the category, tags, and description.
A4: Recommendations Modified
At step 7, the Asset Custodian partially agrees with the recommendations.
The system allows the Asset Custodian to edit the suggested information before applying it.
3.2: Review and Modify AI Classification Recommendations
Use Case ID: UC-08
Use Case Name: Review and Modify AI Classification Recommendations
Related Requirement: FR-11: AI-Assisted Asset Classification
Primary Actor: Asset Custodian
Goal: Allow the Asset Custodian to review, accept, reject, or modify AI-generated asset classification recommendations to ensure that the asset information is accurate and appropriate.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The AI Classification Service has successfully generated classification recommendations for the asset.
Postconditions: The Asset Custodian's accepted or modified classification information is applied to the asset registration form. If the recommendations are rejected, the Asset Custodian can manually enter the classification information. No changes are saved to the asset record until registration is submitted.
Main Success Scenario
1.	The AI Classification Service generates recommended categories, tags, and a standardized description.
2.	The system displays the recommendations to the Asset Custodian.
3.	The Asset Custodian reviews the suggested classification information.
4.	The Asset Custodian selects the recommendations they want to modify.
5.	The system allows the Asset Custodian to edit the category, tags, or description.
6.	The Asset Custodian confirms the modified recommendations.
7.	The system applies the confirmed information to the asset registration form.
8.	The system displays a confirmation message.
Alternative Flows
A1: Recommendations Accepted Without Changes
At step 4, the Asset Custodian accepts all AI recommendations.
The system applies the recommendations without modification.
A2: Recommendations Rejected
At step 4, the Asset Custodian rejects the recommendations.
The system allows manual classification of the asset.
A3: Invalid Modified Information (Exception flow)
At step 6, the system detects invalid or missing required information.
The system displays an error message and asks the Asset Custodian to correct it.
A4: Review Cancelled
The Asset Custodian cancels the review.
The system returns to the registration form without applying the recommendations.
3.3: Regenerate AI Classification Recommendations
Use Case ID: UC-09
Use Case Name: Regenerate AI Classification Recommendations
Related Requirement: FR-11: AI-Assisted Asset Classification
Primary Actor: Asset Custodian
Supporting Actor: AI Classification Service
Goal: Allow the Asset Custodian to request new AI-generated classification recommendations when the initial suggestions are inaccurate, incomplete, or unsuitable for the asset.
Preconditions: The Asset Custodian is logged into the system and has permission to register assets. The AI Classification Service has already generated initial recommendations for the asset.
Postconditions: The AI generates and displays a new set of classification recommendations based on the available or updated asset information. The Asset Custodian can review, accept, or modify the new recommendations before applying them to the registration form.
Main Success Scenario
1.	The Asset Custodian reviews the initial AI-generated classification recommendations.
2.	The Asset Custodian determines that the recommendations are unsuitable.
3.	The Asset Custodian modifies or adds asset information to improve the results.
4.	The Asset Custodian clicks Regenerate Recommendations.
5.	The system sends the updated asset information to the AI Classification Service.
6.	The AI analyzes the information and generates new recommended categories, tags, and a standardized description.
7.	The system displays the new recommendations.
8.	The Asset Custodian reviews the updated recommendations.
9.	The Asset Custodian accepts the recommendations.
10.	The system applies the accepted information to the asset registration form.
Alternative Flows
A1: AI Service Unavailable
At step 5, the AI Classification Service is unavailable. (Exception flow)
The system displays an error message and allows the Asset Custodian to classify the asset manually.
A2: Insufficient Asset Information (Exception flow)
At step 6, the AI cannot generate suitable recommendations.
The system asks the Asset Custodian to provide additional asset information.
A3: Recommendations Rejected
At step 8, the Asset Custodian rejects the new recommendations.
The system allows the Asset Custodian to regenerate recommendations again or manually classify the asset.
A4: Regeneration Cancelled
The Asset Custodian cancels the regeneration process.
The system retains the previously displayed recommendations without applying changes.
AI Declaration: 
AI tools were used to assist in identifying potentially overlooked functional requirements, use cases, and alternative flows to ensure the completeness of our requirements analysis. Additionally, AI was used to generate UML use case diagrams based on descriptions and instructions provided by our team, including the identification of actors, their interactions, and relationships between use cases. All AI-generated suggestions and diagrams were reviewed and refined by the team to ensure accuracy and consistency with the project's requirements.

