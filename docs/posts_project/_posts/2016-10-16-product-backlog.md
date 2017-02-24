---
layout: post
title: Product Backlog
---
|**User Story**|**Cost**|**Priority**|
| :----------- |:----:|  :---:  |
| As maintainer of OEC, I want the application to fetch data from NASA. | 9 | 1 |
| As maintainer of OEC, I want the application to produce a list of changes between the systems in OEC and NASA. | 20 | 1 |
| As maintainer of OEC, I want the application to fetch data from exoplanet.eu. | 2 | 1 |
| As maintainer of OEC, I want the application to produce a list of changes between the systems in OEC and exoplanet.eu. | 2 | 1 |
| As the maintainer of OEC, I want to be notified through a Github pull request about changes to be made to the OEC, changes to the same system from the same catalogue should be combined into one | 15 | 1 |
| As the admin, I want users of this system to be able to approve or reject an update request | 4 | 1 |
| As the maintainer of the OEC, I want the system to specify in the git author field who granted this update | 4 | 1 |
| As the maintainer of the OEC, I want the system to specify in the git commit message where the data came from | 2 | 1 |
|As Professor Rein, only I can grant or revoke permission to use the application.| 6 | 1 |
|As the maintainer of the OEC, I want to be able to preview the diff of the commit that will be made to the OEC before approval| 4 | 1 |
|As the maintainer of the OEC, in the event of a problem during update, the system should provide me with options in it’s own interface to: view the problematic fields, edit the file directly.| 10 | 1 |
|As the maintainer of the OEC, I want to be able to continue the update after fixing any problems| 4 | 1 |
|As a moderator, I want the system to remember my decision, so that if I have previously rejected a request, I won’t be notified of a request for the same data just because it came from a different catalogue.| 10 | 2 |
|As an astrophysicist, I want to be able to manually edit the change if there’s any obvious errors.| 4 | 2 |
|As the admin, I want to be able to view the history of all update requests, including the outcome(approved/rejected) and users who participated that update.| 4 | 3 |
|As the admin, I want confidential user info (api token) to be kept safely| 8 | 4 |
|As an admin, I want the system to accept a new url of a catalogue and start monitoring the field/properties that I specify to the system.| 8 | 5 |
|As an astrophysicist, I want to be instantly emailed about newfound planet or astro systems| 6 | 5 |
|As a student / public user, I want to receive desktop notifications after every updates to systems on the OEC from other catalogues| 6 | 5 |

---

|**Legend**||
|:---|:---|
|Cost|Estimated cost to complete story, in developer hours|
|Priority|Assigned importance, 1 most important, 5 least important|