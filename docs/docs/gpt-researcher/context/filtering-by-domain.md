# Filtering by Domain

If you set Google as a Retriever, you can filter web results by site.

For example, set in the query param you pass the GPTResearcher class instance: `query="site:linkedin.com a python web developer to implement my custom gpt-researcher flow"` will limit the results to linkedin.com

> **Step 1** -  Set these environment variables with a .env file in the root folder

```bash
TAVILY_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=
OPENAI_API_KEY=
DOC_PATH=./my-docs
RETRIEVER=google
GOOGLE_API_KEY=
GOOGLE_CX_KEY=
```

> **Step 2** -  from the root project run:

docker-compose up -- build

> **Step 3** -  from the frontend input box in localhost:3000, you can append any google search filter (such as filtering by domain names)
