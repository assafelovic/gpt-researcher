from __future__ import annotations
import json
from duckduckgo_search import DDGS

ddgs = DDGS()

def web_search(query: str, num_results: int = 4) -> str:
    """Useful for general internet search queries."""
    print("Searching with query {0}...".format(query))
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = ddgs.text(query)
    if not results:
        return json.dumps(search_results)

    total_added = 0
    for j in results:
        search_results.append(j)
        total_added += 1
        if total_added >= num_results:
            break

    return json.dumps(search_results, ensure_ascii=False, indent=4)
