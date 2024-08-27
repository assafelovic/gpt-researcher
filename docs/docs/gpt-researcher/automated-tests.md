# Automated Tests

## Automated Testing with Github Actions

This repository contains the code for the automated testing of the GPT-Researcher Repo using Github Actions. 

The tests are triggered in a docker container which runs the tests via the `pytest` module.

## Running the Tests

You can run the tests:

### Via a docker command

```bash
docker-compose --profile test run --rm gpt-researcher-tests
```

### Via a Github Action

![image](https://github.com/user-attachments/assets/721fca20-01bb-4c10-9cf9-19d823bebbb0)

Attaching here the required settings & screenshots on the github repo level:

Step 1: Within the repo, press the "Settings" tab

Step 2: Create a new environment named "tests" (all lowercase)

Step 3: Click into the "tests" environment & add environment secrets of ```OPENAI_API_KEY``` & ```TAVILY_API_KEY```

Get the keys from here:

https://app.tavily.com/sign-in

https://platform.openai.com/api-keys


![Screen Shot 2024-07-28 at 9 00 19](https://github.com/user-attachments/assets/7cd341c6-d8d4-461f-ab5e-325abc9fe509)
![Screen Shot 2024-07-28 at 9 02 55](https://github.com/user-attachments/assets/a3744f01-06a6-4c9d-8aa0-1fc742d3e866)

If configured correctly, here's what the Github action should look like when opening a new PR or committing to an open PR:

![Screen Shot 2024-07-28 at 8 57 02](https://github.com/user-attachments/assets/30dbc668-4e6a-4b3b-a02e-dc859fc9bd3d)