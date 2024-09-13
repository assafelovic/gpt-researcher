# Docker: Quickstart

> **Step 1** - Install & Open Docker Desktop

Follow instructions at https://www.docker.com/products/docker-desktop/


> **Step 2** - [Follow this flow](https://www.youtube.com/watch?v=x1gKFt_6Us4)

This mainly includes cloning the '.env.example' file, adding your API Keys to the cloned file and saving the file as '.env'

> **Step 3** - Within root, run with Docker.

```bash
docker-compose up --build
```

If that doesn't work, try running it without the dash:
```bash
docker compose up --build
```

> **Step 4** - By default, if you haven't uncommented anything in your docker-compose file, this flow will start 2 processes:
 - the Python server running on localhost:8000
 - the React app running on localhost:3000

Visit localhost:3000 on any browser and enjoy researching!

