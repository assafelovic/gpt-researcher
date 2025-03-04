from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any

import requests


class PubMedCentralSearch:
    """PubMed Central API Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *_: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ):
        """Initializes the PubMedCentralSearch object.

        Args:
            query: The search query.
            query_domains: The domains to search for.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.api_key: str = self._retrieve_api_key()

    def _retrieve_api_key(self) -> str:
        """Retrieves the NCBI API key from environment variables.

        Returns:
            The API key.

        Raises:
            ValueError: If the API key is not found.
        """
        try:
            api_key = os.environ["NCBI_API_KEY"]
        except KeyError:
            raise ValueError(
                "NCBI API key not found. Please set the NCBI_API_KEY environment variable. "
                "You can obtain your key from https://www.ncbi.nlm.nih.gov/account/"
            )
        return api_key

    def fetch(
        self,
        ids: list[str],
    ) -> str:
        """Fetches the full text content for given article IDs.

        Args:
            ids: List of article IDs.

        Returns:
            XML content of the articles.
        """
        base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params: dict[str, Any] = {
            "db": "pmc",
            "id": ",".join(ids),
            "retmode": "xml",
            "api_key": self.api_key,
        }
        response: requests.Response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve data: {response.status_code} - {response.text}")

        return response.text

    def search(
        self,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Searches the query using the PubMed Central API.

        Args:
            max_results: The maximum number of results to return.

        Returns:
            A list of search results.
        """
        base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params: dict[str, Any] = {
            "db": "pmc",
            "term": f"{self.query} AND free fulltext[filter]",
            "retmax": max_results,
            "usehistory": "y",
            "api_key": self.api_key,
            "retmode": "json",
            "sort": "relevance",
        }
        response: requests.Response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: {response.status_code} - {response.text}")

        results: dict[str, Any] = response.json()
        ids: list[str] = results["esearchresult"]["idlist"]

        search_response: list[dict[str, Any]] = []
        for article_id in ids:
            xml_content: str = self.fetch([article_id])
            if self.has_body_content(xml_content):
                article_data: dict[str, Any] | None = self.parse_xml(xml_content)
                if article_data:
                    search_response.append(
                        {
                            "href": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{article_id}/",
                            "body": f"{article_data['title']}\n\n{article_data['abstract']}\n\n{article_data['body'][:500]}...",
                        }
                    )

            if len(search_response) >= max_results:
                break

        return search_response

    def has_body_content(
        self,
        xml_content: str,
    ) -> bool:
        """Checks if the XML content has a body section.

        Args:
            xml_content: XML content of the article.

        Returns:
            Boolean indicating presence of body content.
        """
        root: ET.Element = ET.fromstring(xml_content)
        ns: dict[str, str] = {
            "mml": "http://www.w3.org/1998/Math/MathML",
            "xlink": "http://www.w3.org/1999/xlink",
        }
        article: ET.Element | None = root.find("article", ns)
        if article is None:
            return False

        body_elem: ET.Element | None = article.find(".//body", namespaces=ns)
        if body_elem is not None:
            return True
        else:
            for sec in article.findall(".//sec", namespaces=ns):
                for p in sec.findall(".//p", namespaces=ns):
                    if p.text:
                        return True
        return False

    def parse_xml(
        self,
        xml_content: str,
    ) -> dict[str, Any] | None:
        """Parses the XML content to extract title, abstract, and body.

        Args:
            xml_content: XML content of the article.

        Returns:
            Dictionary containing title, abstract, and body text.
        """
        root: ET.Element = ET.fromstring(xml_content)
        ns: dict[str, str] = {
            "mml": "http://www.w3.org/1998/Math/MathML",
            "xlink": "http://www.w3.org/1999/xlink",
        }

        article: ET.Element | None = root.find("article", ns)
        if article is None:
            return None

        title: str = article.findtext(".//title-group/article-title", default="", namespaces=ns)

        abstract: ET.Element | None = article.find(".//abstract", namespaces=ns)
        abstract_text: str = "".join(abstract.itertext()).strip() if abstract is not None else ""

        body: list[str] = []
        body_elem: ET.Element | None = article.find(".//body", namespaces=ns)
        if body_elem is not None:
            for p in body_elem.findall(".//p", namespaces=ns):
                if p.text:
                    body.append(p.text.strip())
        else:
            for sec in article.findall(".//sec", namespaces=ns):
                for p in sec.findall(".//p", namespaces=ns):
                    if p.text:
                        body.append(p.text.strip())

        return {
            "title": title,
            "abstract": abstract_text,
            "body": "\n".join(body),
        }
