import asyncio
import time

from gpt_researcher.config import Config
from gpt_researcher.context.compression import ContextCompressor
from gpt_researcher.master.functions import *
from gpt_researcher.memory import Memory
from gpt_researcher.utils.enum import ReportType


class GPTResearcher:
    """
    GPT Researcher
    """

    def __init__(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
        source_urls=None,
        config_path=None,
        websocket=None,
        agent=None,
        role=None,
        parent_query: str = "",
        subtopics: list = [],
        visited_urls: set = set()
    ):
        """
        Initialize the GPT Researcher class.
        Args:
            query: str,
            report_type: str
            source_urls
            config_path
            websocket
            agent
            role
            parent_query: str
            subtopics: list
            visited_urls: set
        """
        self.query = query
        self.agent = agent
        self.role = role
        self.report_type = report_type
        self.report_prompt = get_prompt_by_report_type(self.report_type)  # this validates the report type
        self.websocket = websocket
        self.cfg = Config(config_path)
        self.retriever = get_retriever(self.cfg.retriever)
        self.context = []
        self.source_urls = source_urls
        self.memory = Memory(self.cfg.embedding_provider)
        self.visited_urls = visited_urls

        # Only relevant for DETAILED REPORTS
        # --------------------------------------

        # Stores the main query of the detailed report
        self.parent_query = parent_query

        # Stores all the user provided subtopics
        self.subtopics = subtopics

    async def conduct_research(self):
        """
        Runs the GPT Researcher to conduct research
        """
        print(f"🔎 Executando pesquisa para '{self.query}'...")
        
        # Generate Agent
        if not (self.agent and self.role):
            self.agent, self.role = await choose_agent(self.query, self.cfg, self.parent_query)
        await stream_output("logs", self.agent, self.websocket)

        # If specified, the researcher will use the given urls as the context for the research.
        if self.source_urls:
            self.context = await self.get_context_by_urls(self.source_urls)
        else:
            self.context = await self.get_context_by_search(self.query)

        time.sleep(2)

    async def write_report(self, existing_headers: list = []):
        """
        Escreve o relatório baseado na pesquisa realizada

        Returns:
            str: O relatório
        """

        await stream_output("logs", f"✍️ Escrevendo resumo para a tarefa de pesquisa: {self.query}...", self.websocket)

        if self.report_type == "custom_report":
            self.role = self.cfg.agent_role if self.cfg.agent_role else self.role
        elif self.report_type == "subtopic_report":
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                websocket=self.websocket,
                cfg=self.cfg,
                main_topic=self.parent_query,
                existing_headers=existing_headers
            )
        else:
            report = await generate_report(
                query=self.query,
                context=self.context,
                agent_role_prompt=self.role,
                report_type=self.report_type,
                websocket=self.websocket,
                cfg=self.cfg
            )

        return report

    async def get_context_by_urls(self, urls):
        """
            Coleta e comprime o contexto das urls fornecidas
        """
        new_search_urls = await self.get_new_urls(urls)
        await stream_output("logs",
                            f"🧠 Eu vou conduzir minha pesquisa com base nas seguintes urls: {new_search_urls}...",
                            self.websocket)
        scraped_sites = scrape_urls(new_search_urls, self.cfg)
        return await self.get_similar_content_by_query(self.query, scraped_sites)

    async def get_context_by_search(self, query):
        """
           Gera o contexto para a tarefa de pesquisa pesquisando a consulta e coletando os resultados
        Returns:
            context: Lista de contextos
        """
        context = []
        # Generate Sub-Queries including original query
        sub_queries = await get_sub_queries(query, self.role, self.cfg, self.parent_query, self.report_type)

        # If this is not part of a sub researcher, add original query to research for better results
        if self.report_type != "subtopic_report":
            sub_queries.append(query)

        await stream_output("logs",
                            f"🧠 Eu vou conduzir minha pesquisa com base nas seguintes consultas: {sub_queries}...",
                            self.websocket)

        # Using asyncio.gather to process the sub_queries asynchronously
        context = await asyncio.gather(*[self.process_sub_query(sub_query) for sub_query in sub_queries])
        return context

    async def process_sub_query(self, sub_query: str):
        """Recebe uma sub consulta e coleta urls com base nela e reúne o contexto.

        Args:
            sub_query (str): A sub-consulta gerada a partir da consulta original

        Returns:
            str: O contexto coletado a partir da pesquisa
        """
        await stream_output("logs", f"\n🔎 Executando pesquisa para '{sub_query}'...", self.websocket)

        scraped_sites = await self.scrape_sites_by_query(sub_query)
        content = await self.get_similar_content_by_query(sub_query, scraped_sites)

        if content:
            await stream_output("logs", f"📃 {content}", self.websocket)
        else:
            await stream_output("logs", f"🤷 Nenhum conteúdo encontrado para '{sub_query}'...", self.websocket)
        return content

    async def get_new_urls(self, url_set_input):
        """ Obtém novas urls a partir do conjunto de urls fornecido.
        Args: url_set_input (set[str]): O conjunto de urls para obter as novas urls
        Returns: list[str]: As novas urls a partir do conjunto de urls fornecido
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                await stream_output("logs", f"✅ Adicionando url fonte à pesquisa: {url}\n", self.websocket)

                self.visited_urls.add(url)
                new_urls.append(url)

        return new_urls

    async def scrape_sites_by_query(self, sub_query):
        """
        Runs a sub-query
        Args:
            sub_query:

        Returns:
            Summary
        """
        # Get Urls
        retriever = self.retriever(sub_query)
        search_results = retriever.search(
            max_results=self.cfg.max_search_results_per_query)
        new_search_urls = await self.get_new_urls([url.get("href") for url in search_results])

        # Scrape Urls
        # await stream_output("logs", f"📝Scraping urls {new_search_urls}...\n", self.websocket)
        await stream_output("logs", f"🤔 Pesquisando informações relevantes...\n", self.websocket)
        scraped_content_results = scrape_urls(new_search_urls, self.cfg)
        return scraped_content_results

    async def get_similar_content_by_query(self, query, pages):
        await stream_output("logs", f"📝 Obtendo conteúdo relevante com base na consulta: {query}...", self.websocket)
        # Summarize Raw Data
        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.memory.get_embeddings())
        # Run Tasks
        return context_compressor.get_context(query, max_results=8)

    ########################################################################################

    # DETAILED REPORT

    async def write_introduction(self):
        # Construct Report Introduction from main topic research
        introduction = await get_report_introduction(self.query, self.context, self.role, self.cfg, self.websocket)

        return introduction

    async def get_subtopics(self):
        """
        Esta função assíncrona gera subtopicos com base na entrada do usuário e outros parâmetros.

        Returns:
          A função `get_subtopics` está retornando os `subtopicos` que são gerados pela função `construct_subtopics`.
        """
        await stream_output("logs", f"🤔 Gerando subtopicos...", self.websocket)

        subtopics = await construct_subtopics(
            task=self.query,
            data=self.context,
            config=self.cfg,
            # This is a list of user provided subtopics
            subtopics=self.subtopics,
        )

        await stream_output("logs", f"📋subtopicos: {subtopics}", self.websocket)

        return subtopics
