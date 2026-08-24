import os
from typing import Dict, List, Optional

import requests


class SciverseSearch:
    """
    Sciverse API Retriever.

    Sciverse (https://sciverse.space) indexes scientific paper metadata and full
    text, so a search returns passages from paper bodies rather than abstracts
    alone. Each passage carries the id and character offset of the document it
    came from.

    Required environment variable:
    - SCIVERSE_API_TOKEN: request one at https://sciverse.space

    Optional environment variables:
    - SCIVERSE_BASE_URL: defaults to https://api.sciverse.space
    - SCIVERSE_MODE: retrieval mode, "fast" (keyword only), "balanced" (hybrid,
      default) or "quality" (adds LLM query rewriting)
    """

    DEFAULT_BASE_URL = "https://api.sciverse.space"

    # Results carry the retrieved full-text passage in raw_content; scraping
    # the href (usually a DOI or publisher page) would yield less than what
    # semantic search already selected.
    requires_scraping = False

    # Maps the retrieval mode to the API's knobs (`retrieval`: recall backend,
    # `sub_queries`: LLM query-rewrite fan-out).
    MODE_PARAMS = {
        "fast": {"retrieval": "es"},
        "balanced": {"retrieval": "hybrid"},
        "quality": {"retrieval": "hybrid", "sub_queries": 3},
    }

    def __init__(self, query: str, mode: Optional[str] = None, query_domains=None):
        """
        Initialize the SciverseSearch class with a query and retrieval mode.

        :param query: Search query string.
        :param mode: Retrieval mode. One of MODE_PARAMS. "fast" is keyword only,
            "balanced" is hybrid retrieval, "quality" adds LLM query rewriting.
            Defaults to the SCIVERSE_MODE environment variable, then "balanced".
        :param query_domains: Unused; Sciverse searches a curated literature
            corpus rather than the open web.
        """
        self.query = query
        if mode is not None:
            assert mode in self.MODE_PARAMS, f"Invalid mode: {mode}"
            self.mode = mode
        else:
            env_mode = os.environ.get("SCIVERSE_MODE", "balanced")
            if env_mode not in self.MODE_PARAMS:
                print(
                    f"Invalid SCIVERSE_MODE {env_mode!r}; falling back to 'balanced'. "
                    f"Valid values: {sorted(self.MODE_PARAMS)}"
                )
                env_mode = "balanced"
            self.mode = env_mode
        self.query_domains = query_domains
        self.api_key = self._retrieve_api_key()
        self.base_url = (os.environ.get("SCIVERSE_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")

    def _retrieve_api_key(self) -> str:
        """
        Retrieve the Sciverse API token from environment variables.

        :return: The API token.
        :raises Exception: If the API token is not found.
        """
        try:
            return os.environ["SCIVERSE_API_TOKEN"]
        except KeyError:
            raise Exception(
                "Sciverse API token not found. Please set the SCIVERSE_API_TOKEN "
                "environment variable. You can request one at https://sciverse.space/"
            )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Lets Sciverse attribute traffic to this integration.
            "X-Sciverse-Source": "oss_gptresearcher",
        }

    def search(self, max_results: int = 20) -> List[Dict[str, str]]:
        """
        Perform the search on Sciverse and return results.

        Each result carries `raw_content` (title, abstract and the retrieved
        full-text passage) so the research flow can use the passage directly
        instead of scraping the href — which for papers is usually a DOI or
        publisher page behind a paywall.

        :param max_results: Maximum number of passages to retrieve (capped at 100).
        :return: List of dictionaries containing title, href, url, body and
            raw_content of each passage.
        """
        payload = {
            "query": self.query,
            "top_k": min(max_results, 100),
        }
        payload.update(self.MODE_PARAMS[self.mode])

        try:
            response = requests.post(
                f"{self.base_url}/agentic-search",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred while accessing Sciverse API: {e}")
            return []

        payload_json = response.json()
        if not isinstance(payload_json, dict):
            return []
        hits = payload_json.get("hits", [])
        if not isinstance(hits, list):
            return []

        hits = [hit for hit in hits if isinstance(hit, dict)]
        hrefs = self._resolve_hrefs(hits)

        search_result = []
        for hit in hits:
            body = hit.get("chunk") or hit.get("abstract")
            if not body:
                continue
            href = hrefs.get(hit.get("doc_id")) or self._web_href(hit)
            if not href:
                continue
            search_result.append(
                {
                    "title": hit.get("title") or "No Title",
                    "href": href,
                    "url": href,
                    "body": body,
                    "raw_content": self._compose_raw_content(hit),
                }
            )

        return search_result

    @staticmethod
    def _compose_raw_content(hit: dict) -> str:
        """
        Build ready-to-use context so the research flow treats the result as
        prefetched content rather than a URL to scrape (same contract as the
        PubMed Central retriever). The passage is what semantic search selected
        as relevant; scraping a DOI link would usually yield less.

        :param hit: A single search hit.
        :return: Title, abstract and full-text passage as one text block.
        """
        parts = [f"Title: {hit.get('title') or 'No Title'}"]
        if hit.get("abstract"):
            parts.append(f"Abstract: {hit['abstract']}")
        if hit.get("chunk"):
            parts.append(f"Passage from full text: {hit['chunk']}")
        return "\n\n".join(parts)

    def _resolve_hrefs(self, hits: List[dict]) -> Dict[str, str]:
        """
        Look up citable URLs for the hit documents in one metadata query.

        Search hits carry the document id but not its links, so this fetches
        `access_oa_url` and `doi` for all hit doc_ids in a single /meta-search
        call. Prefers the open-access URL, then the DOI, so citations point at
        something a reader can open.

        :param hits: The search hits.
        :return: Mapping of doc_id to URL; empty on lookup failure.
        """
        doc_ids = sorted({hit["doc_id"] for hit in hits if hit.get("doc_id")})
        if not doc_ids:
            return {}

        payload = {
            "filters": [{"field": "doc_id", "operator": "FILTER_OP_IN", "value": doc_ids}],
            "fields": ["doc_id", "access_oa_url", "doi"],
            "page_size": min(len(doc_ids), 200),
        }
        try:
            response = requests.post(
                f"{self.base_url}/meta-search",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            records = response.json().get("results", [])
        except (requests.RequestException, ValueError, AttributeError) as e:
            print(f"An error occurred while resolving Sciverse links: {e}")
            return {}

        hrefs: Dict[str, str] = {}
        for record in records:
            if not isinstance(record, dict) or not record.get("doc_id"):
                continue
            href = self._pick_href(record)
            if href:
                hrefs[record["doc_id"]] = href
        return hrefs

    @staticmethod
    def _pick_href(record: dict) -> Optional[str]:
        """
        Prefer the open-access URL, then the DOI.

        :param record: A metadata record holding access_oa_url and doi.
        :return: A URL, or None when the record carries no addressable source.
        """
        oa_url = record.get("access_oa_url")
        if isinstance(oa_url, list):
            oa_url = oa_url[0] if oa_url else None
        if oa_url:
            return oa_url

        doi = record.get("doi")
        if doi:
            return doi if doi.startswith("http") else f"https://doi.org/{doi}"

        return None

    @staticmethod
    def _web_href(hit: dict) -> Optional[str]:
        """
        Fall back to the crawl source URL for web hits without a doc_id.

        :param hit: A single search hit.
        :return: An http(s) URL, or None.
        """
        source = hit.get("source")
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            return source
        return None
