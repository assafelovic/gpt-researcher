# Retriever Plugins

GPT Researcher can use a search provider that ships as its own Python package. Install the package, set `RETRIEVER` to the name it registers, and it is used like any built-in retriever. No change to GPT Researcher is needed.

This is the recommended way to add a new search provider. The core project keeps a small set of built-in retrievers; a plugin lets a provider ship, version and support its integration on its own schedule.

## Using a plugin

```bash
pip install gptr-acme-retriever
export RETRIEVER=acme
```

Plugins can be combined with built-in retrievers, e.g. `RETRIEVER=acme,duckduckgo`. Built-in names always take precedence, so a plugin cannot replace `tavily`, `google` or any other shipped retriever.

## Community retrievers

These plugins are distributed and maintained separately from GPT Researcher.
Install them in the same Python environment as GPT Researcher.

| Retriever | Package | Maintainer and support |
| --- | --- | --- |
| Sciverse | [`gpt-researcher-sciverse`](https://pypi.org/project/gpt-researcher-sciverse/) | [Sciverse-Agent-Tools](https://github.com/opendatalab/Sciverse-Agent-Tools) · [Issues](https://github.com/opendatalab/Sciverse-Agent-Tools/issues) |

### Sciverse

[Sciverse](https://sciverse.space/) retrieves scientific literature passages and
resolves citation links through its metadata API. Requires Python 3.12+ and
GPT Researcher 0.16.1+ (installed as a package dependency).

```bash
pip install gpt-researcher-sciverse
export RETRIEVER=sciverse
export SCIVERSE_API_TOKEN="your-sciverse-token"
```

Obtain an API token at [sciverse.space](https://sciverse.space/). Optional settings:

- `SCIVERSE_MODE`: `fast` for keyword retrieval, `balanced` (default) for hybrid
  keyword/vector retrieval, or `quality` for hybrid retrieval with query rewriting.
- `SCIVERSE_BASE_URL`: defaults to `https://api.sciverse.space`.
- Combine with a built-in retriever, e.g. `RETRIEVER=sciverse,duckduckgo`.

Results provide already-retrieved passages under `raw_content`, together with
available titles and abstracts. These are excerpts, **not complete papers**.
The plugin declares `requires_scraping=False` so this evidence is used directly
rather than fetching the citation's publisher page. It accepts `query_domains`
for interface compatibility but **does not apply domain filtering**.

See the [plugin documentation](https://github.com/opendatalab/Sciverse-Agent-Tools/blob/main/packages/gpt-researcher/README.md)
for configuration and development details. API access and integration support
are provided by the plugin maintainer.

## Writing a plugin

A plugin is a class with the same shape as the built-in retrievers, registered under the `gpt_researcher.retrievers` [entry-point group](https://packaging.python.org/en/latest/specifications/entry-points/).

```python
# acme_retriever/__init__.py
import os
import requests

from gpt_researcher.retrievers.base import BaseRetriever


class AcmeSearch(BaseRetriever):
    # True: results are links that GPT Researcher should scrape.
    # False: results already carry the page text under "raw_content".
    requires_scraping = True

    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []
        self.api_key = os.environ["ACME_API_KEY"]

    def search(self, max_results=7):
        try:
            response = requests.get(
                "https://api.acme.example/search",
                params={"q": self.query, "limit": max_results},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            response.raise_for_status()
            items = response.json().get("results", [])
        except (requests.RequestException, ValueError):
            return []
        return [
            {"href": item["url"], "body": item.get("snippet", "")}
            for item in items
            if item.get("url")
        ]
```

```toml
# pyproject.toml
[project]
name = "gptr-acme-retriever"
version = "0.1.0"
dependencies = ["gpt-researcher", "requests"]

[project.entry-points."gpt_researcher.retrievers"]
acme = "acme_retriever:AcmeSearch"
```

The entry-point name (`acme` above) is the value users put in `RETRIEVER`.

### The contract

- `__init__(self, query, query_domains=None)` receives the sub-query and any domain filter.
- `search(self, max_results=7)` returns a list of dicts. Each needs a URL under `href` (or `url`) and may carry a short `body` snippet.
- Set `requires_scraping = False` only if every result includes the full page text under `raw_content`; GPT Researcher will then use it without fetching the page.
- Return `[]` on network or parsing errors instead of raising, so one failing provider does not abort a research run.

If a plugin fails to import, GPT Researcher logs a warning and falls back to the default retriever. Use the snippet in [Testing your Retriever](./test-your-retriever.md) to check your results.
