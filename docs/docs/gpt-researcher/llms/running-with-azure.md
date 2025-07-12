# Running with Azure

## Example: Azure OpenAI Configuration

If you are not using OpenAI's models, but other model providers, besides the general configuration above, also additional environment variables are required.

Here is an example for [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models) configuration:

```bash
OPENAI_API_VERSION="2024-05-01-preview" # or whatever you are using
AZURE_OPENAI_ENDPOINT="https://CHANGEMEN.openai.azure.com/" # change to the name of your deployment
AZURE_OPENAI_API_KEY="[Your Key]" # change to your API key

EMBEDDING="azure_openai:text-embedding-ada-002" # change to the deployment of your embedding model

FAST_LLM="azure_openai:gpt-4o-mini" # change to the name of your deployment (not model-name)
FAST_TOKEN_LIMIT=4000

SMART_LLM="azure_openai:gpt-4o" # change to the name of your deployment (not model-name)
SMART_TOKEN_LIMIT=4000

RETRIEVER="bing" # if you are using Bing as your search engine (which is likely if you use Azure)
BING_API_KEY="[Your Key]"
```

For more details on what each variable does, you can check out the [GPTR Config Docs](https://docs.gptr.dev/docs/gpt-researcher/gptr/config)