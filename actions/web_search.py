from __future__ import annotations
import json
from duckduckgo_search import DDGS
from tavily import Client
from langchain.utilities import SearxSearchWrapper
import os
from config import Config

CFG = Config()


def web_search(query: str, num_results: int = 4) -> str:
    """Useful for general internet search queries."""
    print("Searching with query {0}...".format(query))
    search_results = []
    search_response = []
    if not query:
        return json.dumps(search_results)

    if CFG.search_api == "tavily":
        tavily_search = Client(os.environ["TAVILY_API_KEY"])
        results = tavily_search.search(query, search_depth="basic").get("results", [])
        # Normalizing results to match the format of the other search APIs
        search_response = [{"href": obj["url"], "body": obj["content"]} for obj in results]
    elif CFG.search_api == "searx":
        searx = SearxSearchWrapper(searx_host=os.environ["SEARX_URL"])
        results = searx.results(query, num_results)
        # Normalizing results to match the format of the other search APIs
        search_response = [{"href": obj["link"], "body": obj["snippet"]} for obj in results]
    elif CFG.search_api == "duckduckgo":
        ddgs = DDGS()
        search_response = ddgs.text(query)

    total_added = 0
    for j in search_response:
        search_results.append(j)
        total_added += 1
        if total_added >= num_results:
            break

    return json.dumps(search_results, ensure_ascii=False, indent=4)
