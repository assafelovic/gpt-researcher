import os
import xml.etree.ElementTree as ET

import requests


class PubMedCentralSearch:
    """
    PubMed Central API Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the PubMedCentralSearch object.
        Args:
            query: The search query.
        """
        self.query = query
        self.api_key = self._retrieve_api_key()

    def _retrieve_api_key(self):
        """
        Retrieves the NCBI API key from environment variables.
        Returns:
            The API key.
        Raises:
            Exception: If the API key is not found.
        """
        try:
            api_key = os.environ["NCBI_API_KEY"]
        except KeyError:
            raise Exception(
                "NCBI API key not found. Please set the NCBI_API_KEY environment variable. "
                "You can obtain your key from https://www.ncbi.nlm.nih.gov/account/"
            )
        return api_key

    def search(self, max_results=10):
        """
        Searches the query using the PubMed Central API.
        Args:
            max_results: The maximum number of results to return.
        Returns:
            A list of search results.
        """
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pmc",
            "term": f"{self.query} AND free fulltext[filter]",
            "retmax": max_results,
            "usehistory": "y",
            "api_key": self.api_key,
            "retmode": "json",
            "sort": "relevance"
        }
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(
                f"Failed to retrieve data: {response.status_code} - {response.text}"
            )

        results = response.json()
        ids = results["esearchresult"]["idlist"]

        search_response = []
        for article_id in ids:
            xml_content = self.fetch([article_id])
            if self.has_body_content(xml_content):
                article_data = self.parse_xml(xml_content)
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

    def fetch(self, ids):
        """
        Fetches the full text content for given article IDs.
        Args:
            ids: List of article IDs.
        Returns:
            XML content of the articles.
        """
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pmc",
            "id": ",".join(ids),
            "retmode": "xml",
            "api_key": self.api_key,
        }
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(
                f"Failed to retrieve data: {response.status_code} - {response.text}"
            )

        return response.text

    def has_body_content(self, xml_content):
        """
        Checks if the XML content has a body section.
        Args:
            xml_content: XML content of the article.
        Returns:
            Boolean indicating presence of body content.
        """
        root = ET.fromstring(xml_content)
        ns = {
            "mml": "http://www.w3.org/1998/Math/MathML",
            "xlink": "http://www.w3.org/1999/xlink",
        }
        article = root.find("article", ns)
        if article is None:
            return False

        body_elem = article.find(".//body", namespaces=ns)
        if body_elem is not None:
            return True
        else:
            for sec in article.findall(".//sec", namespaces=ns):
                for p in sec.findall(".//p", namespaces=ns):
                    if p.text:
                        return True
        return False

    def parse_xml(self, xml_content):
        """
        Parses the XML content to extract title, abstract, and body.
        Args:
            xml_content: XML content of the article.
        Returns:
            Dictionary containing title, abstract, and body text.
        """
        root = ET.fromstring(xml_content)
        ns = {
            "mml": "http://www.w3.org/1998/Math/MathML",
            "xlink": "http://www.w3.org/1999/xlink",
        }

        article = root.find("article", ns)
        if article is None:
            return None

        title = article.findtext(
            ".//title-group/article-title", default="", namespaces=ns
        )

        abstract = article.find(".//abstract", namespaces=ns)
        abstract_text = (
            "".join(abstract.itertext()).strip() if abstract is not None else ""
        )

        body = []
        body_elem = article.find(".//body", namespaces=ns)
        if body_elem is not None:
            for p in body_elem.findall(".//p", namespaces=ns):
                if p.text:
                    body.append(p.text.strip())
        else:
            for sec in article.findall(".//sec", namespaces=ns):
                for p in sec.findall(".//p", namespaces=ns):
                    if p.text:
                        body.append(p.text.strip())

        return {"title": title, "abstract": abstract_text, "body": "\n".join(body)}
