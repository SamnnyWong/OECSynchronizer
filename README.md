OEC Synchronizer [Team 09 CSC01 Project]
--------------

[![MIT](http://img.shields.io/badge/license-MIT-green.svg?style=flat)](http://opensource.org/licenses/MIT)

Team website: [Team MASK](http://teammask.github.io)


Project Requirements
---
##### Python 3.5+, git


Setup Instructions
---
Run `pip3 install -r requirements.txt` to install dependencies.
If you don't have admin privilege, try `pip3 install --user -r requirements.txt` instead.


For Deliverable 2
---
[Personas and User stories](https://teammask.github.io/posts_personas_stories/2016/10/02/professor-rein.html)
* Each persona/user story page is listed in the side panel


For Deliverable 3
--- 
### Plan
* [Product Backlog](https://teammask.github.io/posts_project/2016/10/16/product-backlog.html)
* [Release Plan](https://teammask.github.io/posts_project/2016/10/16/Release-plan.html)
* [Sprint 1 Backlog](https://teammask.github.io/posts_project/2016/10/16/sprint-1-backlog.html)

### Result
* Release: [oec_sync](oec_sync)
* Design Description (UML): [design.png](design.png)
* [Sprint 1 Retrospective and Results](https://teammask.github.io/posts_project/2016/10/23/Sprint-1-Retrospective.html)


For Deliverable 4
--- 
### Sprint plan and results
* [Sprint 2](https://teammask.github.io/posts_project/2016/10/30/sprint-2-backlog.html)
* [Sprint 3](https://teammask.github.io/posts_project/2016/11/06/sprint-3-backlog.html)
* [Sprint 4](https://teammask.github.io/posts_project/2016/11/13/sprint-4-backlog.html)
* [Sprint 2-4 Retrospective](https://teammask.github.io/posts_project/2016/11/13/Sprint-2-4-Retrospective.html)

### System design
* [System design UML](design/system_design.png)
* [System description](design/system_documentation.md)

### UI design
* [Mock up](design/UI_design.png)

### Code Inspection Video
* https://youtu.be/i6yfiFHRvpg

Individual code inspection documents can be found at [code_inspection](code_inspection)

For Deliverable 5
---
### Sprint plan and results
* [Sprint 5](https://teammask.github.io/posts_project/2016/11/20/sprint-5-backlog.html)
* [Sprint 6](https://teammask.github.io/posts_project/2016/11/29/sprint-6-backlog.html)
* [Sprint 5-6 & Project Retrospective](https://teammask.github.io/posts_project/2016/11/30/Sprint-5-6-Retrospective.html)

### System design
* [System design UML](design/system_design.png)
* [System description](design/system_documentation.md)

### Code Inspection 2 Video
* https://youtu.be/a94krD3-jfU

Individual code inspection documents can be found at [code_inspection2](code_inspection2)

### Running the application
After you have cloned/pulled latest

**NOTE:** See Project Requirements above

1. cd into project home team09-project

2. install dependencies

   `pip3 install --user -r requirements.txt` 
   
   or as admin
   
   `pip3 install -r requirements.txt`
   
3. set python path

   WINDOWS:
	```batch
	for /f "delims=" %F in ('cd') do set TEAM09_ROOT=%F
	set TEAM09_SOURCE=oec_sync\sync
	set TEAM09_TESTS=oec_sync\tests
	set TEAM09_GUI=oec_sync\gui
	set PYTHONPATH=%TEAM09_ROOT%\%TEAM09_SOURCE%;%TEAM09_ROOT%\%TEAM09_TESTS%;%TEAM09_ROOT%\%TEAM09_GUI%
	```
   \*NIX:
	```bash
	export TEAM09_ROOT=`pwd`
	export TEAM09_SOURCE=oec_sync/sync
	export TEAM09_TESTS=oec_sync/tests
	export TEAM09_GUI=oec_sync/gui
	export PYTHONPATH=${TEAM09_ROOT}/${TEAM09_SOURCE}:${TEAM09_ROOT}/${TEAM09_TESTS}:${TEAM09_ROOT}/${TEAM09_GUI}
	```
 
4. run application (`cd` into `oec_sync`) 
	- **GUI (interactive)**: `python3 driver.py config.yml`
	- **command-line (interactive)**: `python3 driver.py --cli config.yml`
	- **command-line (automatic/bot)**: `python3 driver.py --cli --auto MAX`
		+ `MAX` is the max number of requests that will be created, suggest using a small number (e.g. `3`) for testing

### Testing the application

**NOTE:** Instructions here assume you have at least executed Steps 1 - 3 of previous instruction set "Running the application"

Tests can be found in the **team09-project\oec_sync\tests** directory

There are three categories of tests as grouped in folders:

- **Acceptance:** This folder contains a `guidelines.md` file for testing the application based on user data
- **Component:**  Contains tests that test individual components. A component can be tested by running the associated test script. (i.e test_&lt;module name goes here>). All component tests can be run by running the `run_component.py` script
	```
	$ python3 run_component.py
	``` 

- **Integration:** Contains tests that test compatibility of different components that work together. An integration test can be run by running the associated test script. All integration tests can be run by running the `run_integration.py` script
	```
	$ python3 run_integration.py
	```

Finally, all tests can be run at once by running python run_all_tests in the home directory of tests (i.e **team09-project\oec_sync\tests** )
```
$ python3 run_all_tests.py
```

License
--------------
Copyright (c) 2016 TeamMask, University of Toronto, Scarborough

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

