import asyncio
from typing import List, Dict, Optional, Set

from ...context.compression import ContextCompressor, WrittenContentCompressor, VectorstoreCompressor
from ...document import DocumentLoader, LangChainDocumentLoader
from ...utils.enum import ReportSource
from ..actions.utils import stream_output


class ContextManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def get_context(self):
        """Retrieve context based on source URLs if available."""
        if self.researcher.source_urls:
            return await self.__get_context_by_urls(self.researcher.source_urls)
        elif self.researcher.report_source == ReportSource.Local.value:
            return await self.__get_context_from_local_documents()
        elif self.researcher.report_source == ReportSource.Hybrid.value:
            return await self.__get_hybrid_context()
        elif self.researcher.report_source == ReportSource.LangChainDocuments.value:
            return await self.__get_context_from_langchain_documents()
        elif self.researcher.report_source == ReportSource.LangChainVectorStore.value:
            return await self.__get_context_by_vectorstore(self.researcher.query, self.researcher.vector_store_filter)
        else:
            return await self.__get_context_by_search(self.researcher.query)

    async def __get_context_by_urls(self, urls):
        new_search_urls = await self.__get_new_urls(urls)
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "source_urls",
                f"🗂️ I will conduct my research based on the following urls: {new_search_urls}...",
                self.researcher.websocket,
            )

        scraped_sites = await self.researcher.scraper.scrape_urls(new_search_urls)
        
        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_sites)
        

        return await self.get_similar_content_by_query(self.researcher.query, scraped_sites)

    async def __get_context_from_local_documents(self):
        document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
        if self.researcher.vector_store:
            self.researcher.vector_store.load(document_data)

        return await self.__get_context_by_search(self.researcher.query, document_data)

    async def __get_hybrid_context(self):
        document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
        if self.researcher.vector_store:
            self.researcher.vector_store.load(document_data)

        docs_context = await self.__get_context_by_search(self.researcher.query, document_data)
        web_context = await self.__get_context_by_search(self.researcher.query)
        return f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

    async def __get_context_from_langchain_documents(self):
        langchain_documents_data = await LangChainDocumentLoader(self.researcher.documents).load()
        
        if self.researcher.vector_store:
            self.researcher.vector_store.load(langchain_documents_data)
        

        return await self.__get_context_by_search(self.researcher.query, langchain_documents_data)

    async def __get_context_by_vectorstore(self, query, filter: Optional[dict] = None):
        sub_queries = await self.__get_sub_queries(query)
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                sub_queries,
            )

        context = await asyncio.gather(
            *[self.__process_sub_query_with_vectorstore(sub_query, filter) for sub_query in sub_queries]
        )
        return context

    async def __get_context_by_search(self, query, scraped_data: list = []):
        sub_queries = await self.__get_sub_queries(query)
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ I will conduct my research based on the following queries: {sub_queries}...",
                self.researcher.websocket,
                True,
                sub_queries,
            )

        context = await asyncio.gather(
            *[self.__process_sub_query(sub_query, scraped_data) for sub_query in sub_queries]
        )
        return context

    async def __process_sub_query_with_vectorstore(self, sub_query: str, filter: Optional[dict] = None):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_with_vectorstore_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        content = await self.__get_similar_content_by_query_with_vectorstore(sub_query, filter)

        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def __process_sub_query(self, sub_query: str, scraped_data: list = []):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 Running research for '{sub_query}'...",
                self.researcher.websocket,
            )

        if not scraped_data:
            scraped_data = await self.researcher.scraper.scrape_data_by_query(sub_query)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_data)


        content = await self.get_similar_content_by_query(sub_query, scraped_data)

        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 No content found for '{sub_query}'...",
                self.researcher.websocket,
            )
        return content

    async def __get_new_urls(self, url_set_input):
        new_urls = []
        for url in url_set_input:
            if url not in self.researcher.visited_urls:
                self.researcher.visited_urls.add(url)
                new_urls.append(url)
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "added_source_url",
                        f"✅ Added source url to research: {url}\n",
                        self.researcher.websocket,
                        True,
                        url,
                    )
        return new_urls

    async def __get_similar_content_by_query_with_vectorstore(self, query, filter):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )

        vectorstore_compressor = VectorstoreCompressor(
            self.researcher.vector_store, filter)
        return await vectorstore_compressor.async_get_context(
            query=query, max_results=8
        )

    async def get_similar_content_by_query(self, query, pages):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"📚 Getting relevant content based on query: {query}...",
                self.researcher.websocket,
            )

        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.researcher.memory.get_embeddings()
        )
        return await context_compressor.async_get_context(
            query=query, max_results=10, cost_callback=self.researcher.add_costs
        )

    async def __get_sub_queries(self, query):
        from gpt_researcher.master.actions import get_sub_queries
        return await get_sub_queries(
            query=query,
            agent_role_prompt=self.researcher.role,
            cfg=self.researcher.cfg,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
        )

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        all_queries = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> Set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents))

        results = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents = set().union(*results)
        relevant_contents = list(relevant_contents)[:max_results]

        if relevant_contents and self.researcher.verbose:
            prettier_contents = "\n".join(relevant_contents)
            await stream_output(
                "logs", "relevant_contents_context", f"📃 {prettier_contents}", self.researcher.websocket
            )

        return relevant_contents

    async def __get_similar_written_contents_by_query(self,
                                                      query: str,
                                                      written_contents: List[Dict],
                                                      similarity_threshold: float = 0.5,
                                                      max_results: int = 10
                                                      ) -> List[str]:
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_relevant_written_content",
                f"🔎 Getting relevant written content based on query: {query}...",
                self.researcher.websocket,
            )

        written_content_compressor = WrittenContentCompressor(
            documents=written_contents,
            embeddings=self.researcher.memory.get_embeddings(),
            similarity_threshold=similarity_threshold
        )
        return await written_content_compressor.async_get_context(
            query=query, max_results=max_results, cost_callback=self.researcher.add_costs
        )
