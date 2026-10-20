# Configuration

The config.py enables you to customize GPT Researcher to your specific needs and preferences.

Thanks to our amazing community and contributions, GPT Researcher supports multiple LLMs and Retrievers.
In addition, GPT Researcher can be tailored to various report formats (such as APA), word count, research iterations depth, etc.

GPT Researcher defaults to our recommended suite of integrations: [OpenAI](https://platform.openai.com/docs/overview) for LLM calls and [Tavily API](https://app.tavily.com) for retrieving real-time web information.

## Choosing an LLM

GPT Researcher's writer turns scraped sources into a report, so how faithfully a model sticks to its sources matters more than general benchmark scores. The table below comes from Vectara's [Hallucination Leaderboard](https://github.com/vectara/hallucination-leaderboard), which has each model summarize 7,700+ articles (news, science, medicine, law, business and more) using only the source text, then checks every summary for claims the source doesn't support with the HHEM-2.3 evaluation model.

A selection of models you can configure in GPT Researcher, ordered by hallucination rate (lower is better). Data as of September 22, 2026; see the leaderboard for all 100+ models.

| Model | Provider | Hallucination rate | Factual consistency | Answer rate |
|---|---|---:|---:|---:|
| GPT-5.4 nano | OpenAI | 3.1% | 96.9% | 100.0% |
| Gemini 2.5 Flash-Lite | Google | 3.3% | 96.7% | 99.5% |
| Llama 3.3 70B | Meta | 4.1% | 95.9% | 99.5% |
| Mistral Large (24.11) | Mistral | 4.5% | 95.5% | 99.9% |
| GPT-5.4 mini | OpenAI | 5.5% | 94.5% | 100.0% |
| GPT-4.1 | OpenAI | 5.6% | 94.4% | 99.9% |
| DeepSeek V3.2 | DeepSeek | 6.3% | 93.7% | 92.6% |
| GPT-6 Sol | OpenAI | 6.5% | 93.5% | 100.0% |
| GPT-5.4 | OpenAI | 7.0% | 93.0% | 99.9% |
| Gemini 2.5 Pro | Google | 7.0% | 93.0% | 99.1% |
| Gemini 2.5 Flash | Google | 7.8% | 92.2% | 99.0% |
| Llama 4 Maverick | Meta | 8.2% | 91.8% | 100.0% |
| DeepSeek V4 Pro | DeepSeek | 8.6% | 91.4% | 97.2% |
| GPT-5.5 | OpenAI | 9.3% | 90.7% | 100.0% |
| Claude Haiku 4.5 | Anthropic | 9.8% | 90.2% | 99.5% |
| Gemini 3.1 Pro (preview) | Google | 10.4% | 89.6% | 99.4% |
| Claude Sonnet 4.6 | Anthropic | 10.6% | 89.4% | 99.9% |
| Qwen 3.5 Plus | Alibaba | 10.7% | 89.3% | 99.8% |
| Kimi K2.6 | Moonshot | 10.8% | 89.2% | 99.7% |
| Claude Opus 4.7 | Anthropic | 12.0% | 88.0% | 98.0% |
| gpt-oss-120b | OpenAI | 14.2% | 85.8% | 99.9% |
| Grok 4.1 Fast | xAI | 17.8% | 82.2% | 98.5% |

- **Hallucination rate**: share of summaries containing a claim not supported by the source.
- **Answer rate**: share of articles the model agreed to summarize.

GPT Researcher defaults to `gpt-5.4` for `SMART_LLM` and `STRATEGIC_LLM`, and `gpt-5.4-mini` for `FAST_LLM`. This benchmark measures faithfulness to sources, not reasoning or writing quality: smaller models often rank well here partly because their summaries add less. Use it to narrow your choice, then compare reports on your own queries (see [Testing your LLM](../llms/testing-your-llm.md)).

The default config.py file can be found in `/gpt_researcher/config/`. It supports various options for customizing GPT Researcher to your needs.
You can also include your own external JSON file `config.json` by adding the path in the `config_path` param.
The config JSON should follow the format/keys in the default config. Below is a sample config.json file to help get you started:
```json
{
  "RETRIEVER": "tavily",
  "EMBEDDING": "openai:text-embedding-3-small",
  "SIMILARITY_THRESHOLD": 0.42,
  "CONTEXT_FILTER": "auto",
  "FAST_LLM": "openai:gpt-5.4-mini",
  "SMART_LLM": "openai:gpt-5.4",
  "STRATEGIC_LLM": "openai:gpt-5.4",
  "LANGUAGE": "english",
  "CURATE_SOURCES": false,
  "FAST_TOKEN_LIMIT": 3000,
  "SMART_TOKEN_LIMIT": 6000,
  "STRATEGIC_TOKEN_LIMIT": 4000,
  "BROWSE_CHUNK_MAX_LENGTH": 8192,
  "SUMMARY_TOKEN_LIMIT": 700,
  "TEMPERATURE": 0.4,
  "DOC_PATH": "./my-docs",
  "REPORT_SOURCE": "web"
}
```


For example, to start GPT-Researcher and specify a specific config you would do this:
```bash
python gpt_researcher/main.py --config_path my_config.json
```




 **Please follow the config.py file for additional future support**.

Below is a list of current supported options:

- **`RETRIEVER`**: Search engine or research retriever used for retrieving sources. Defaults to `tavily`. Options include `tavily`, `duckduckgo`, `bing`, `brave`, `google`, `searchapi`, `serper`, `serpapi`, `searx`, `arxiv`, `openalex`, `semantic_scholar`, `pubmed_central`, `exa`, `crw`, `groundroute`, `bocha`, `xquik`, `custom`, and `mcp`. You can also combine retrievers with commas, such as `tavily,openalex,semantic_scholar`. [Check here](https://github.com/assafelovic/gpt-researcher/tree/master/gpt_researcher/retrievers) for supported retrievers
- **`EMBEDDING`**: Embedding model. Defaults to `openai:text-embedding-3-small`. Options: `ollama`, `huggingface`, `azure_openai`, `custom`.
- **`SIMILARITY_THRESHOLD`**: Threshold value for similarity comparison when processing documents. Defaults to `0.42`.
- **`CONTEXT_FILTER`**: How scraped content is filtered before it reaches the writer: `auto` (default; Jev when `TYPESAFE_API_KEY` is set, otherwise keyword ranking), `jev`, `keyword`, `embeddings` or `none`. No mode requires an embeddings provider except `embeddings`. See [Context Filter](./context-filter.md).
- **`FAST_LLM`**: Model name for fast LLM operations such summaries. Defaults to `openai:gpt-5.4-mini`.
- **`SMART_LLM`**: Model name for smart operations like generating research reports and reasoning. Defaults to `openai:gpt-5.4`.
- **`STRATEGIC_LLM`**: Model name for strategic operations like generating research plans and strategies. Defaults to `openai:gpt-5.4`.
- **`LANGUAGE`**: Language to be used for the final research report. Defaults to `english`.
- **`CURATE_SOURCES`**: Whether to curate sources for research. This step adds an LLM run which may increase costs and total run time but improves quality of source selection. Defaults to `False`.
- **`FAST_TOKEN_LIMIT`**: Maximum token limit for fast LLM responses. Defaults to `3000`.
- **`SMART_TOKEN_LIMIT`**: Maximum token limit for smart LLM responses. Defaults to `6000`.
- **`STRATEGIC_TOKEN_LIMIT`**: Maximum token limit for strategic LLM responses. Defaults to `4000`.

#### Recommended values for modern long-output models

The default token limits are calibrated for GPT-4o-class models
(16k max output). For models with larger output capacity, increase
these limits to avoid truncated reports:

| Model family            | Max output | Recommended SMART_TOKEN_LIMIT |
|-------------------------|-----------:|------------------------------:|
| GPT-4o / GPT-4.1        |        16k |                          8000 |
| Claude Haiku 4.5        |        64k |                         16000 |
| Claude Sonnet 4.6       |        64k |                         16000 |
| Claude Opus 4.7         |       128k |                         32000 |
| GPT-5 family            |       128k |                         32000 |

Apply proportional values to `FAST_TOKEN_LIMIT` and
`STRATEGIC_TOKEN_LIMIT` if you use distinct models for those roles.
The hard upper bound is 200k (sanity guard against typos).

- **`BROWSE_CHUNK_MAX_LENGTH`**: Maximum length of text chunks to browse in web sources. Defaults to `8192`.
- **`SUMMARY_TOKEN_LIMIT`**: Maximum token limit for generating summaries. Defaults to `700`.
- **`TEMPERATURE`**: Sampling temperature for LLM responses, typically between 0 and 1. A higher value results in more randomness and creativity, while a lower value results in more focused and deterministic responses. Defaults to `0.4`.
- **`USER_AGENT`**: Custom User-Agent string for web crawling and web requests.
- **`MAX_SEARCH_RESULTS_PER_QUERY`**: Maximum number of search results to retrieve per query. Defaults to `5`.
- **`MEMORY_BACKEND`**: Backend used for memory operations, such as local storage of temporary data. Defaults to `local`.
- **`TOTAL_WORDS`**: Total word count limit for document generation or processing tasks. Defaults to `1200`.
- **`REPORT_FORMAT`**: Preferred format for report generation. Defaults to `APA`. Consider formats like `MLA`, `CMS`, `Harvard style`, `IEEE`, etc.
- **`MAX_ITERATIONS`**: Maximum number of iterations for processes like query expansion or search refinement. Defaults to `3`.
- **`AGENT_ROLE`**: Role of the agent. This configures the behavior of specialized research agents. Defaults to `None`. When set, it activates role-specific prompting and techniques tailored to particular research domains.
- **`MAX_SUBTOPICS`**: Maximum number of subtopics to generate or consider. Defaults to `3`.
- **`SCRAPER`**: Web scraper to use for gathering information. Defaults to `bs` (BeautifulSoup). You can also use [newspaper](https://github.com/codelucas/newspaper).
- **`MAX_SCRAPER_WORKERS`**: Maximum number of concurrent scraper workers per research. Defaults to `15`.
- **`REPORT_SOURCE`**: Source for the research report data. Defaults to `web` for online research. Can be set to `doc` for local document-based research. This determines where GPT Researcher gathers its primary information from.
- **`DOC_PATH`**: Path to read and research local documents. Defaults to `./my-docs`.
- **`PROMPT_FAMILY`**: The family of prompts and prompt formatting to use. Defaults to prompting optimized for GPT models. See the full list of options in [enum.py](https://github.com/assafelovic/gpt-researcher/blob/master/gpt_researcher/utils/enum.py#L56).
- **`LLM_KWARGS`**: Json formatted dict of additional keyword args to be passed to the LLM provider class when instantiating it. This is primarily useful for clients like Ollama that allow for additional keyword arguments such as `num_ctx` that influence the inference calls.
- **`EMBEDDING_KWARGS`**: Json formatted dict of additional keyword args to be passed to the embedding provider class when instantiating it.
- **`DEEP_RESEARCH_BREADTH`**: Controls the breadth of deep research, defining how many parallel paths to explore. Defaults to `3`.
- **`DEEP_RESEARCH_DEPTH`**: Controls the depth of deep research, defining how many sequential searches to perform. Defaults to `2`.
- **`DEEP_RESEARCH_CONCURRENCY`**: Controls the concurrency level for deep research operations. Defaults to `4`.
- **`REASONING_EFFORT`**: Controls the reasoning effort of strategic models. Default to `medium`.

## Deep Research Configuration

The deep research parameters allow you to fine-tune how GPT Researcher explores complex topics that require extensive knowledge gathering. These parameters work together to determine the thoroughness and efficiency of the research process:

- **`DEEP_RESEARCH_BREADTH`**: Controls how many parallel research paths are explored simultaneously. A higher value (e.g., 5) causes the researcher to investigate more diverse subtopics at each step, resulting in broader coverage but potentially less focus on core themes. The default value of `3` provides a balanced approach between breadth and depth.

- **`DEEP_RESEARCH_DEPTH`**: Determines how many sequential search iterations GPT Researcher performs for each research path. A higher value (e.g., 3-4) allows for following citation trails and diving deeper into specialized information, but increases research time substantially. The default value of `2` ensures reasonable depth while maintaining practical completion times.

- **`DEEP_RESEARCH_CONCURRENCY`**: Sets how many concurrent operations can run during deep research. Higher values speed up the research process on capable systems but may increase API rate limit issues or resource consumption. The default value of `4` is suitable for most environments, but can be increased on systems with more resources or decreased if you experience performance issues.

For academic or highly specialized research, consider increasing both breadth and depth (e.g., BREADTH=4, DEPTH=3). For quick exploratory research, lower values (e.g., BREADTH=2, DEPTH=1) will provide faster results with less detail.

To change the default configurations, you can simply add env variables to your `.env` file as named above or export manually in your local project directory.

For example, to manually change the search engine and report format:

```bash
export RETRIEVER=bing
export REPORT_FORMAT=IEEE
```

For academic literature reviews, you can combine web and scholarly retrievers:

```bash
export RETRIEVER=tavily,openalex,semantic_scholar
```

Please note that you might need to export additional env vars and obtain API keys for other supported search retrievers and LLM providers. Please follow your console logs for further assistance.
To learn more about additional LLM support you can check out the docs [here](/docs/gpt-researcher/llms/llms).
