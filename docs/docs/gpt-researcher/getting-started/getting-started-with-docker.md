# Docker: Quickstart

> **Step 1** - Install & Open Docker Desktop

Follow instructions at https://www.docker.com/products/docker-desktop/


> **Step 2** - [Follow this flow](https://www.youtube.com/watch?v=x1gKFt_6Us4)

This mainly includes cloning the '.env.example' file, adding your API Keys to the cloned file and saving the file as '.env'

In `requirements.txt` add the relevant langchain packages for the LLM your choose (langchain-google-genai, langchain-deepseek, langchain_mistralai for example)

> **Step 3** - Within root, run with Docker.

```bash
docker-compose -f docker-compose.yml -f docker-compose.env.yml up --build
```

If that doesn't work, try running it without the dash:
```bash
docker compose -f docker-compose.yml -f docker-compose.env.yml up --build
```

The root `.env` is excluded from Docker build contexts. Include
`docker-compose.env.yml` to supply all its settings to the backend containers at
runtime, including `RETRIEVER`, `SMART_LLM`, and provider-specific options. The
override uses the string `env_file` format supported by older Compose releases.
Existing `environment` entries in the base file override `env_file` values;
exported shell values take precedence for entries resolved from the environment.

If you use exported shell variables without a `.env` file, omit the override:

```bash
docker compose up --build
# Or: docker-compose up --build
```

The base file passes only the variables listed in its `environment` sections.
Add any other exported settings there when using the shell-only flow. Unset
`RETRIEVER` and `SMART_LLM` use the application's defaults.

The ignore rule only excludes the root `.env`, preserving `.env.example` and
frontend environment files used by `Dockerfile.fullstack`. Next.js build-time
settings must still be available when building the frontend. Do not put backend
credentials in frontend configuration files.

> **Step 4** - By default, if you haven't uncommented anything in your docker-compose file, this flow will start 2 processes:
 - the Python server running on localhost:8000
 - the React app running on localhost:3000

Visit localhost:3000 on any browser and enjoy researching!


## Running with the Docker CLI

If you want to run the Docker container without using docker-compose, you can use the following command:

```bash
docker run -it --name gpt-researcher -p 8000:8000 --env-file .env  -v /absolute/path/to/gptr_docs:/my-docs  gpt-researcher
```

This will run the Docker container and mount the `/gptr_docs` directory to the container's `/my-docs` directory for analysis by the GPTR API Server.
