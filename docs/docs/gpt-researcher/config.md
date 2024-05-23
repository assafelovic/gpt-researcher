# Introduction

The config.py enables you to customize GPT Researcher to your specific needs and preferences.

Thanks to our amazing community and contributions, GPT Researcher supports multiple LLMs and Retrievers.
In addition, GPT Researcher can be tailored to various report formats (such as APA), word count, research iterations depth, etc.

GPT Researcher defaults to our recommended suite of integrations: [OpenAI](https://platform.openai.com/docs/overview) for LLM calls and [Tavily API](https://app.tavily.com) for retrieving realtime online information.

As seen below, OpenAI still stands as the superior LLM. We assume it will stay this way for some time, and that prices will only continue to decrease, while performance and speed increase over time.

<div style={{ marginBottom: '10px' }}>
<img align="center" height="350" src="/img/leaderboard.png" />
</div>

Here is an example of the default config.py file found in `/gpt_researcher/config/`:

```python
import os
def __init__(self, config_file: str = None):
    """Initialize the config class."""
    self.config_file = os.path.expanduser(config_file) if config_file else os.getenv('CONFIG_FILE')
    self.retriever = os.getenv('RETRIEVER', "tavily")
    self.embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
    self.llm_provider = os.getenv('LLM_PROVIDER', "openai")
    self.fast_llm_model = os.getenv('FAST_LLM_MODEL', "gpt-3.5-turbo-16k")
    self.smart_llm_model = os.getenv('SMART_LLM_MODEL', "gpt-4o")
    self.fast_token_limit = int(os.getenv('FAST_TOKEN_LIMIT', 2000))
    self.smart_token_limit = int(os.getenv('SMART_TOKEN_LIMIT', 4000))
    self.browse_chunk_max_length = int(os.getenv('BROWSE_CHUNK_MAX_LENGTH', 8192))
    self.summary_token_limit = int(os.getenv('SUMMARY_TOKEN_LIMIT', 700))
    self.temperature = float(os.getenv('TEMPERATURE', 0.55))
    self.user_agent = os.getenv('USER_AGENT', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                               "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0")
    self.max_search_results_per_query = int(os.getenv('MAX_SEARCH_RESULTS_PER_QUERY', 5))
    self.memory_backend = os.getenv('MEMORY_BACKEND', "local")
    self.total_words = int(os.getenv('TOTAL_WORDS', 800))
    self.report_format = os.getenv('REPORT_FORMAT', "APA")
    self.max_iterations = int(os.getenv('MAX_ITERATIONS', 3))
    self.agent_role = os.getenv('AGENT_ROLE', None)
    self.scraper = os.getenv("SCRAPER", "bs")
    self.max_subtopics = os.getenv("MAX_SUBTOPICS", 3)
    self.doc_path = os.getenv("DOC_PATH", "")
```
To change the default configurations, you can simply add env variables to your `.env` file as named in the config.py file.

Please note that you can also include your own external JSON file `config.json` by adding the path in the `config_file` param.

To learn more about additional LLM support you can check out the docs [here](/docs/gpt-researcher/llms).

You can also change the search engine by modifying the `retriever` param to others such as `duckduckgo`, `bing`, `google`, `serper`, `searx` and more. [Check here](https://github.com/assafelovic/gpt-researcher/tree/master/gpt_researcher/retrievers) for supported retrievers.

Please note that you might need to sign up and obtain an API key for any of the other supported retrievers and LLM providers.