   
**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**
###Guidelines for testing product acceptance.

###Current Sprint: #4

**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**

**NOTE:** Subscribe to this repository: https://github.com/teammask/open_exoplanet_catalogue

**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**
            
**USER STORY:** #1 As the maintainer of the OEC, I want the application to fetch data from NASA

**USER STORY:** #2 As the maintainer of the OEC, I want the application to produce a list of changes between the systems in OEC and NASA
            
**----------------------------------------The following sequence of steps verify the above user stor(y/ies)----------------------------------------**

The stories above are an operation unit. i.e the application fetches data from
NASA and Exoplanet catalogue and produce a list of changes between OEC and
these systems.

**STEPS:**

1. The  `team09-Project/oec_sync/sync_config/` contains configuration files for all catalogues that can be monitored by this application. 
2. Open NASA.yml, confirm the `ignore` property is set to `False`.
3. Open exoplanet.yml, confirm the `ignore` property is set to `True`. We currently do not fully support this catalogue
4. The `team09-Project/oec_sync/config.yml` is the configuration file for the application
5. run `python3 driver.py ../config` from `team09-Project/oec_sync/sync/`
6. Verify that the application has fetched and listed difference from NASA catalogue

**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**

**USER STORY:** #3 As the maintainer of OEC, I want to be notified through a Github pull request about changes to be made to the OEC, changes to the same system from the same  catalogue should be combined into one

**USER STORY:** #9 As the maintainer of the OEC, I want to be able to preview the diff of the commit that will be made to the OEC before approval

**USER STORY:** #10 As Matthias, In the event of a problem during update, the system should provide me with options in it’s own interface to: view the problematic fields, edit the file directly.

**USER STORY:** #13 As an astrophysicist, I want to be able to manually edit the change if there’s any obvious errors.

**USER STORY:** #11 As Matthias, I want to be able to continue the update after fixing any problems

**----------------------------------------The following sequence of steps verify the above user stor(y/ies)----------------------------------------**

**STEPS:**

At this time, the application has presented you with a prompt:

`0). Edit and submit an update request`

`1). Discard changes and exit the program`

1. Enter 0. Press enter to answer the prompt.
2. The next prompt asks to choose which update request to work with
3. Select any of your choosing: This is user story #9
4. The new prompt asks to submit this request
5. For the purpose of testing choose, Enter y, Press enter to answer the prompt
6. The next prompt allows you to launch an editor to make any changes (if necessary). 
7. Enter y and press Enter to answer the prompt. You should be forwarded to your editor. This is user stories #10 and #13
8.  After saving the changes if any, the next prompt asks if you have finished and ready to submit. Enter y and press enter to submit. This is user story #11
9. If you are subscribed to the repository, you will receive a pull request notification. This is User story #3

**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**

**USER STORY:** #5 As the maintainer of the OEC, I want the system to specify in the git  author field who granted this update

**USER STORY:** #6 As the maintainer of the OEC, I want the system to specify in the git  commit message where the data came from


**----------------------------------------The following sequence of steps verify the above user stor(y/ies)----------------------------------------**

The stories above are an operation unit. i.e the application sets the author and git commit message at the same time.

**STEPS:**

1. Verify that the commits in the PR created specify in the commit message where the changes come from
2. Merge the pull request. Verify that the author field is set to the email in the commit

**---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------**
