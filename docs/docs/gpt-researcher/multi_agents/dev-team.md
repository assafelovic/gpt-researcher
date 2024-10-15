# AI Dev Team

The AI Dev Team is our multi_agents flow, leveraging Langgraph & GPTResearcher, to generate code with the power of AI.

To run the AI Dev Team, you'll need to set up the following environment variables in your `.env` file:

```bash
PGVECTOR_CONNECTION_STRING=
GITHUB_TOKEN=
```

For asyncronous [Langchain Vector Stores](https://python.langchain.com/v0.2/docs/integrations/vectorstores/pgvector/), the PGVECTOR_CONNECTION_STRING should contain the string `+psycopg`, for example: `postgresql+psycopg://...`. 

This is currently appended within the python script itself, so you can set your postgres connection string as usual: `postgresql://...` in the env file for the asyncronous PGVector tasks.

The `GITHUB_TOKEN` env var is your Github  Personal Access Token. To generate your Github  Personal Access Token:


> **Step 1** - Click on your profile picture in the top-right corner of GitHub and select "Settings".

> **Step 2** - In the left sidebar, click on "Developer settings".

> **Step 3** - In the left sidebar, click on "Developer settings". Click on "Personal access tokens", then "Tokens (classic)".
Click "Generate new token" and select the appropriate scopes for your needs. The ability to read repos should be enough.

> **Step 4** - Copy the generated token. Paste the token you generated into the `GITHUB_TOKEN` env variable.

> **Step 5** - Click "Add secret" in the Github Admin to save it.
