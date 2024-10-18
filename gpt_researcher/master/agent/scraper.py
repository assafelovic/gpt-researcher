import asyncio
from typing import List, Dict
from ..actions import scrape_urls


class ReportScraper:
    def __init__(self, researcher):
        self.researcher = researcher

    async def scrape_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape content from a list of URLs.

        Args:
            urls (List[str]): List of URLs to scrape.

        Returns:
            List[Dict]: List of scraped content results.
        """
        if self.researcher.verbose:
            await self.researcher.stream_output(
                "logs",
                "scraping_urls",
                f"🌐 Scraping content from {len(urls)} URLs...",
                self.researcher.websocket,
            )

        scraped_content = await asyncio.to_thread(scrape_urls, urls, self.researcher.cfg)

        if self.researcher.verbose:
            await self.researcher.stream_output(
                "logs",
                "scraping_complete",
                f"✅ Scraping complete. Retrieved content from {len(scraped_content)} sources.",
                self.researcher.websocket,
            )

        return scraped_content

    async def scrape_data_by_query(self, query: str) -> List[Dict]:
        """
        Search for URLs based on a query and scrape their content.

        Args:
            query (str): The query to search for.

        Returns:
            List[Dict]: List of scraped content results.
        """
        if self.researcher.verbose:
            await self.researcher.stream_output(
                "logs",
                "searching_query",
                f"🔍 Searching for relevant URLs for query: '{query}'...",
                self.researcher.websocket,
            )

        search_urls = await self._search_urls(query)
        new_search_urls = await self._get_new_urls(search_urls)

        if self.researcher.verbose:
            await self.researcher.stream_output(
                "logs",
                "scraping_query_urls",
                f"🌐 Scraping content from {len(new_search_urls)} URLs found for query: '{query}'...",
                self.researcher.websocket,
            )

        scraped_content = await self.scrape_urls(new_search_urls)

        return scraped_content

    async def _search_urls(self, query: str) -> List[str]:
        """
        Search for URLs based on a query using configured retrievers.

        Args:
            query (str): The query to search for.

        Returns:
            List[str]: List of URLs found.
        """
        search_urls = []
        for retriever_class in self.researcher.retrievers:
            retriever = retriever_class(query)
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.researcher.cfg.max_search_results_per_query
            )
            search_urls.extend([url.get("href") for url in search_results])
        return search_urls

    async def _get_new_urls(self, urls: List[str]) -> List[str]:
        """
        Filter out already visited URLs and add new ones to the visited set.

        Args:
            urls (List[str]): List of URLs to filter.

        Returns:
            List[str]: List of new, unvisited URLs.
        """
        new_urls = []
        for url in urls:
            if url not in self.researcher.visited_urls:
                self.researcher.visited_urls.add(url)
                new_urls.append(url)
                if self.researcher.verbose:
                    await self.researcher.stream_output(
                        "logs",
                        "added_source_url",
                        f"✅ Added source URL to research: {url}\n",
                        self.researcher.websocket,
                        True,
                        url,
                    )
        return new_urls
