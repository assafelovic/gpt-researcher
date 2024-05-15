# Customization

The config.py enables you to customize GPT Researcher to your specific needs and preferences.

Thanks to our amazing community and contributions, GPT Researcher supports multiple LLMs and Retrievers.
In addition, GPT Researcher can be tailored to various report formats (such as APA), word count, research iterations depth, etc.

GPT Researcher defaults to our recommended suite of integrations: [OpenAI](https://platform.openai.com/docs/overview) for LLM calls and [Tavily API](https://app.tavily.com) for retrieving realtime online information.

As seen below, OpenAI still stands as the superior LLM. We assume it will stay this way for some time, and that prices will only continue to decrease, while performance and speed increase over time.

<div style={{ marginBottom: '10px' }}>
<img align="center" height="350" src="/img/leaderboard.png" />
</div>

It may not come as a surprise that our default search engine is [Tavily](https://app.tavily.com). We're aimed at building our search engine to tailor the exact needs of searching and aggregating for the most factual and unbiased information for research tasks.
We highly recommend using it with GPT Researcher, and more generally with LLM applications that are built with RAG. To learn more about our search API [see here](/docs/tavily-api/introduction)

Here is an example of the default config.py file found in `/gpt_researcher/config/`:

```python
def __init__(self, config_file: str = None):
    self.config_file = config_file
    self.retriever = "tavily"
    self.llm_provider = "openai"
    self.fast_llm_model = "gpt-3.5-turbo"
    self.smart_llm_model = "gpt-4o"
    self.fast_token_limit = 2000
    self.smart_token_limit = 4000
    self.browse_chunk_max_length = 8192
    self.summary_token_limit = 700
    self.temperature = 0.6
    self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                      " Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    self.memory_backend = "local"
    self.total_words = 1000
    self.report_format = "apa"
    self.max_iterations = 1

    self.load_config_file()
```

Please note that you can also include your own external JSON file by adding the path in the `config_file` param.

To learn more about additional LLM support you can check out the [Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai) and [Langchain supported LLMs](https://python.langchain.com/docs/integrations/llms/) documentation. Simply pass different provider names in the `llm_provider` config param.

You can also change the search engine by modifying the `retriever` param to others such as `duckduckgo`, `googleAPI`, `googleSerp`, `searx` and more. 

Please note that you might need to sign up and obtain an API key for any of the other supported retrievers and LLM providers.