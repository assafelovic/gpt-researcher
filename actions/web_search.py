from __future__ import annotations
import os
import json
import requests
from duckduckgo_search import DDGS
from tavily import Client
from langchain.utilities import SearxSearchWrapper
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

    elif CFG.search_api == "googleSerp":
        return serp_web_search(os.environ["SERP_API_KEY"], query, num_results)
    
    elif CFG.search_api == "googleAPI":
        return google_web_search(os.environ["GOOGLE_API_KEY"], os.environ["GOOGLE_CX"], query, num_results)
    
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

def serp_web_search(serp_api_key:str, query: str, num_results: int = 10) -> str:
    """Useful for general internet search queries using the Serp API."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        "X-API-KEY": serp_api_key,
        "Content-Type": "application/json",
    }

    resp = requests.request("POST", url, headers=headers, data=payload)
    if resp is None:
        return
    try:
        search_results = json.loads(resp.text)
    except Exception:
        return
    if search_results is None:
        return

    results = search_results["organic"]
    search_results = []

    # Normalizing results to match the format of the other search APIs
    for result in results:
        # skip youtube results
        if "youtube.com" in result["link"]:
            continue
        search_result = {
            "title": result["title"],
            "href": result["link"],
            "body": result["snippet"],
        }
        search_results.append(search_result)
    print("Searching with query {0}...".format(query))
    return json.dumps(search_results, ensure_ascii=False, indent=4)


def google_web_search(google_api_key:str, google_cx:str, query: str, num_result: int = 10) -> str:
    """Useful for general internet search queries using the Google API."""

    url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_cx}&q={query}&start=1"
    resp = requests.get(url)

    if resp is None:
        return
    try:
        search_results = json.loads(resp.text)
    except Exception:
        return
    if search_results is None:
        return

    results = search_results.get("items", [])
    search_results = []

    # Normalizing results to match the format of the other search APIs
    for result in results:
        # skip youtube results
        if "youtube.com" in result["link"]:
            continue
        search_result = {
            "title": result["title"],
            "href": result["link"],
            "body": result["snippet"],
        }
        search_results.append(search_result)

    print("Searching with query {0}...".format(query))

    return json.dumps(search_results[:num_result], ensure_ascii=False, indent=4)