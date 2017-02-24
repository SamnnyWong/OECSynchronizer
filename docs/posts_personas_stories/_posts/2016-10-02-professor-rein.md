---
layout: post
title: Professor Hanno Rein
---

### Persona
* 30-year-old astrophysics professor, male
* Works at an university campus 9-5, but often works additional hours to respond to student emails and appointments
* Busy schedule, so wants things to be done automatically with minimal human interaction
* Wants to keep informed with everything that happens around him
* Likes things to be direct and to the point, won't have time to read lengthy emails or notifications
* Likes things to be formal and serious
* Knowledgeable in both astrophysics and computer science
* Familiar with UNIX systems and open source projects on Github
* Keeps work and personal life separate 

### User Stories
* As maintainer of OEC, I want the application to fetch data from NASA.
* As maintainer of OEC, I want the application to produce a list of changes between the systems in OEC and NASA.
* As maintainer of OEC, I want the application to fetch data from exoplanet.eu.
* As maintainer of OEC, I want the application to produce a list of changes between the systems in OEC and exoplanet.eu.
* As the maintainer of OEC, I want to be notified through a Github pull request about changes to be made to the OEC, changes to the same system from the same catalogue should be combined into one.
* As the admin, I want users of this system to be able to approve or reject an update request.
* I am the only one who can grant or revoke permission to use the application.
* I want the system to accept a new url of a catalogue and start monitoring the field/properties that I specify to the system. 
* As a moderator, I want the system to remember my decision, so that if I have previously rejected a request, I won’t be notified of a request for the same data just because it came from a different catalogue.
* As the maintainer of the OEC, I want the system to specify in the git commit message where the data came from.
As the maintainer of the OEC, I want the system to specify in the git author field who granted this update.
* As the maintainer of the OEC, I want to be able to preview the diff of the commit that will be made to the OEC before approval
* As the admin, I want to be able to view the history of all update requests, including the outcome(approved/rejected) and users who participated that update.
* As the admin, I want confidential user info (api token) to be kept safely.