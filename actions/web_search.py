from __future__ import annotations
import json
from duckduckgo_search import DDGS

def web_search(query: str, num_results: int = 8) -> str:
    """Useful for general internet search queries."""
    print("Searching with query {0}...".format(query))
    search_results = []

    try:
        ddgs = DDGS()
        results = ddgs.text(query)
    except AssertionError:
        # This is the error that we are trying to catch.
        traceback_str = f"Traceback (most recent call last):\n{repr(e)}"
        print("Ignoring error:", traceback_str)
        return json.dumps(search_results)

    if results is None:
        return json.dumps({"error": "error in getting vqd"})

    results = list(results)

    total_added = 0
    for j in results:
        search_results.append(j)
        total_added += 1
        if total_added >= num_results:
            break


    return json.dumps(search_results, ensure_ascii=False, indent=4)