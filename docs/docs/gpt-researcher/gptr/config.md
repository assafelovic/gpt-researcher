# Configuration

The config.py enables you to customize GPT Researcher to your specific needs and preferences.

Thanks to our amazing community and contributions, GPT Researcher supports multiple LLMs and Retrievers.
In addition, GPT Researcher can be tailored to various report formats (such as APA), word count, research iterations depth, etc.

GPT Researcher defaults to our recommended suite of integrations: [OpenAI](https://platform.openai.com/docs/overview) for LLM calls and [Tavily API](https://app.tavily.com) for retrieving real-time web information.

As seen below, OpenAI still stands as the superior LLM. We assume it will stay this way for some time, and that prices will only continue to decrease, while performance and speed increase over time.

<div style={{ marginBottom: '10px' }}>
<img align="center" height="350" src="/img/leaderboard.png" />
</div>

The default config.py file can be found in `/gpt_researcher/config/`. It supports various options for customizing GPT Researcher to your needs.
You can also include your own external JSON file `config.json` by adding the path in the `config_file` param. **Please follow the config.py file for additional future support**.

Below is a list of current supported options:

- **`RETRIEVER`**: Web search engine used for retrieving sources. Defaults to `tavily`. Options: `duckduckgo`, `bing`, `google`, `searchapi`, `serper`, `searx`. [Check here](https://github.com/assafelovic/gpt-researcher/tree/master/gpt_researcher/retrievers) for supported retrievers
- **`EMBEDDING`**: Embedding model. Defaults to `openai:text-embedding-3-small`. Options: `ollama`, `huggingface`, `azure_openai`, `custom`.
- **`FAST_LLM`**: Model name for fast LLM operations such summaries. Defaults to `openai:gpt-4o-mini`.
- **`SMART_LLM`**: Model name for smart operations like generating research reports and reasoning. Defaults to `openai:gpt-4o`.
- **`STRATEGIC_LLM`**: Model name for strategic operations like generating research plans and strategies. Defaults to `openai:o1-preview`.
- **`FAST_TOKEN_LIMIT`**: Maximum token limit for fast LLM responses. Defaults to `2000`.
- **`SMART_TOKEN_LIMIT`**: Maximum token limit for smart LLM responses. Defaults to `4000`.
- **`BROWSE_CHUNK_MAX_LENGTH`**: Maximum length of text chunks to browse in web sources. Defaults to `8192`.
- **`SUMMARY_TOKEN_LIMIT`**: Maximum token limit for generating summaries. Defaults to `700`.
- **`TEMPERATURE`**: Sampling temperature for LLM responses, typically between 0 and 1. A higher value results in more randomness and creativity, while a lower value results in more focused and deterministic responses. Defaults to `0.55`.
- **`TOTAL_WORDS`**: Total word count limit for document generation or processing tasks. Defaults to `800`.
- **`REPORT_FORMAT`**: Preferred format for report generation. Defaults to `APA`. Consider formats like `MLA`, `CMS`, `Harvard style`, `IEEE`, etc.
- **`MAX_ITERATIONS`**: Maximum number of iterations for processes like query expansion or search refinement. Defaults to `3`.
- **`AGENT_ROLE`**: Role of the agent. This might be used to customize the behavior of the agent based on its assigned roles. No default value.
- **`MAX_SUBTOPICS`**: Maximum number of subtopics to generate or consider. Defaults to `3`.
- **`SCRAPER`**: Web scraper to use for gathering information. Defaults to `bs` (BeautifulSoup). You can also use [newspaper](https://github.com/codelucas/newspaper).
- **`DOC_PATH`**: Path to read and research local documents. Defaults to an empty string indicating no path specified.
- **`USER_AGENT`**: Custom User-Agent string for web crawling and web requests.
- **`MEMORY_BACKEND`**: Backend used for memory operations, such as local storage of temporary data. Defaults to `local`.

To change the default configurations, you can simply add env variables to your `.env` file as named above or export manually in your local project directory.

For example, to manually change the search engine and report format:
```bash
export RETRIEVER=bing
export REPORT_FORMAT=IEEE
```
Please note that you might need to export additional env vars and obtain API keys for other supported search retrievers and LLM providers. Please follow your console logs for further assistance.
To learn more about additional LLM support you can check out the docs [here](/docs/gpt-researcher/llms/llms).

You can also include your own external JSON file `config.json` by adding the path in the `config_file` param.

## Example: Azure OpenAI Configuration

If you are not using OpenAI's models, but other model providers, besides the general configuration above, also additional environment variables are required.
Check the [langchain documentation](https://python.langchain.com/v0.2/docs/integrations/platforms/) about your model for the exact configuration of the API keys and endpoints.

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
