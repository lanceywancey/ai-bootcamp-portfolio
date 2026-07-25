AI REVIEW BOOTCAMP - DAY 8, QUESTION 1
======================================

AI Review, Docker, Jenkins, C++, Python, and CI Verification


1. PURPOSE
----------

This project demonstrates a small AI-assisted software verification workflow.
It combines:

- a Flask web application;
- a C++ multiplication program;
- Python verification scripts;
- Docker Compose;
- a Jenkins CI pipeline;
- intentional failure and regression-detection activities.

The main lesson is:

AI can generate or modify code quickly, but correctness must be supported by
review, executable tests, repeatable builds, and CI evidence.


2. PROJECT FILES
----------------

Day_8_Q1/

  app_multiply.py
      Flask web application. It calls the compiled C++ executable twice,
      obtains the results, adds them using Python, and displays the results in
      a browser.

  cpp/multiply.cpp
      C++ command-line program. It accepts two integer arguments and prints
      their product.

  python/check_multiply.py
      Python verification script. It runs the compiled C++ program with
      multiple inputs, compares actual and expected results, and returns a
      non-zero exit status when a test fails.

  test_basic.py
      Small pytest smoke test. It confirms that the Python testing stage is
      operational before the pipeline compiles and verifies the C++ program.

  requirements.txt
      Python packages required by the Flask application.

  Dockerfile
      Builds the Flask application image. It installs Python dependencies and
      the C++ compiler required by the application container.

  Dockerfile.jenkins
      Builds the Jenkins image. It installs Python, pytest, g++, and make so
      Jenkins can test Python code and compile C++ source.

  docker-compose.yml
      Defines the Flask and Jenkins services, port mappings, project mounts,
      and the persistent Jenkins data volume.

  Jenkinsfile
      Defines the Jenkins pipeline stages:

      1. Python smoke test
      2. C++ compilation with warnings enabled
      3. Python verification of the compiled C++ program

  README.txt
      This guide.


3. PREREQUISITES
----------------

Install and prepare:

- Docker Desktop
- A modern web browser
- A text editor or IDE
- An approved AI tool for the AI-review activities

Start Docker Desktop and wait until the Docker Engine is running.

Verify Docker from Terminal:

    docker info
    docker compose version


4. START THE PROJECT
--------------------

Open Terminal and change to the extracted project directory:

    cd /path/to/Day_8_Q1

Build the images and start both services:

    docker compose up --build -d

The first build may take several minutes.

Check service status:

    docker compose ps

Expected services:

- faculty-training-app: host port 60001 -> container port 5000
- jenkins:              host port 60002 -> container port 8080
- Jenkins agent port:   host port 50000 -> container port 50000


5. VERIFY THE FLASK APPLICATION
-------------------------------

The application container automatically compiles cpp/multiply.cpp when it
starts.

Confirm that the Linux executable exists:

    docker compose exec faculty-training-app ls -l /app/multiply

Run it directly:

    docker compose exec faculty-training-app /app/multiply 3 4

Expected output:

    12

Open the Flask application:

    http://localhost:60001

Expected browser content:

    AI Review CI/CD Demo
    C++ result 1: 3 x 4 = 12
    C++ result 2: 5 x 6 = 30
    Python sum: 12 + 30 = 42

Do not compile a macOS executable and copy it into the Linux container. The
container must use a Linux executable.


6. FIRST-TIME JENKINS SETUP
---------------------------

Open Jenkins:

    http://localhost:60002

For a new Jenkins installation, retrieve the initial administrator password:

    docker compose exec jenkins \
      cat /var/jenkins_home/secrets/initialAdminPassword

In the browser:

1. Paste the password into the Unlock Jenkins page.
2. Select Install suggested plugins.
3. Wait for plugin installation to finish.
4. Create the first administrator username and password.
5. Save the Jenkins URL.
6. Select Start using Jenkins.

Jenkins stores accounts, plugins, jobs, and build history in the persistent
jenkins_home Docker volume. If Jenkins was configured previously, sign in with
the existing account instead.


7. CREATE THE JENKINS PIPELINE
------------------------------

Complete these steps in the Jenkins web interface:

1. From the dashboard, select New Item.
2. Enter the job name:

       phase3-python-test

3. Select Pipeline, then select OK.
4. In the Pipeline section, set Definition to Pipeline script.
5. Open Jenkinsfile in a text editor.
6. Copy its complete contents into the Jenkins Script box.
7. Select Save.

The Jenkins container sees the project source at /workspace. The classroom
exercise uses a bind mount so Jenkins immediately sees saved source changes.

In a production CI system, a commit or pull request normally triggers the
pipeline, which checks out a clean source revision from Git. The pipeline then
compiles from source and runs its checks. A precompiled executable normally
does not need to be committed to Git.


8. RUN THE PIPELINE
-------------------

Open the phase3-python-test job and select Build Now.

Students do not manually compile C++ before selecting Build Now. The pipeline
compiles the latest saved source during every build.

Open the newly created build, normally labelled #1. Select Console Output if it
is not displayed automatically. The exact menu layout may vary between Jenkins
versions.

Expected successful evidence includes:

    1 passed

    g++ -Wall -Wextra cpp/multiply.cpp -o multiply

    3 * 4 = 12
    0 * 0 = 0
    -3 * 4 = -12
    -3 * -4 = 12
    ALL TESTS PASSED
    Finished: SUCCESS

A successful pipeline means that the configured checks passed. It does not
prove that every possible input or requirement has been tested.


9. AI REVIEW AND REGRESSION ACTIVITY
------------------------------------

Step A - Expand the tests

1. Ask an approved AI tool to propose additional multiplication test cases.
2. For every proposed case, review the input, expected output, and rationale.
3. Add at least four reviewed cases to python/check_multiply.py.
4. Save the file.
5. Select Build Now in Jenkins.
6. Confirm ALL TESTS PASSED and Finished: SUCCESS.

Step B - Introduce an intentional defect

Change this correct line in cpp/multiply.cpp:

    std::cout << (a * b) << std::endl;

to an intentionally incorrect line, for example:

    std::cout << (a + b) << std::endl;

Save the file. Do not compile manually. Select Build Now again. Jenkins will
compile the changed source and run the verification script.

Capture evidence showing:

- the failed cases;
- TEST FAILURE;
- Finished: FAILURE.

Step C - AI-assisted diagnosis

Before submitting console output to an AI tool:

- remove or hide passwords;
- remove or hide tokens and credentials;
- remove personal or restricted data;
- include only the relevant source, expected behaviour, and failure output;
- follow institutional policy and use an approved AI service.

Ask the AI tool to identify the root cause, propose a minimal fix, and suggest
a regression test. Treat AI findings as hypotheses, not independent proof.

Step D - Restore and verify

Restore the correct multiplication expression:

    a * b

Save the file and select Build Now again. Confirm that the final build returns
to Finished: SUCCESS. Do not submit the project with the intentional bug.


10. FLASK APPLICATION AFTER A C++ CHANGE
----------------------------------------

Jenkins compiles a fresh /workspace/multiply executable during every pipeline
build. The Flask container uses its own /app/multiply executable.

If you want the Flask page to use the latest restored C++ source, restart the
application service:

    docker compose restart faculty-training-app

The application startup command will compile the current source again.


11. LOGS AND TROUBLESHOOTING
----------------------------

Show recent logs and return to the Terminal prompt:

    docker compose logs --tail 50 faculty-training-app
    docker compose logs --tail 50 jenkins

Follow new Jenkins logs continuously:

    docker compose logs -f jenkins

Press Control+C to stop following logs. This does not stop Jenkins.

If Terminal output appears frozen after accidentally pressing Control+S:

    Press Control+Q, then Control+C.

If /app/multiply is missing:

    docker compose logs --tail 50 faculty-training-app
    docker compose down
    docker compose up --build -d

If Jenkins does not respond after the Mac wakes from sleep:

    docker compose ps
    docker compose restart jenkins
    docker compose logs --tail 30 jenkins

Wait until the logs report that Jenkins is fully up and running. Then open a
new browser tab at http://localhost:60002.


12. STOP OR RESET THE PROJECT
-----------------------------

Stop and remove the containers and project network while preserving Jenkins
data:

    docker compose down

Start the project again later:

    docker compose up -d

Completely reset Jenkins, including accounts, plugins, jobs, and build history:

    docker compose down -v

WARNING: The -v option permanently deletes this project's Jenkins volume.


13. EXPECTED EVIDENCE AND DELIVERABLES
--------------------------------------

- Screenshot of the working Flask page
- Screenshot or Console Output from a successful Jenkins build
- At least four additional reviewed test cases
- Screenshot or Console Output from the intentional failed build
- AI diagnosis notes with sensitive information removed or hidden
- Comparison of AI review findings
- Final successful build after restoring the correct implementation
- Short reflection on what CI proved and what it did not prove


END OF README
