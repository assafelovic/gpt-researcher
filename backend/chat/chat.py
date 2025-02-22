from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING, Any

from gpt_researcher.config import Config
from gpt_researcher.memory import Memory
from gpt_researcher.utils.llm import get_llm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import tool
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.runnables.config import RunnableConfig
from langchain_core.vectorstores.base import VectorStoreRetriever
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

if TYPE_CHECKING:
    from fastapi import WebSocket
    from langchain.tools import BaseTool
    from langchain_core.language_models import BaseChatModel


class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        config_path: os.PathLike | str,
        headers: dict[str, Any] | None = None,
        vector_store: InMemoryVectorStore | None = None,
    ):
        self.report: str = report
        self.headers: dict[str, Any] | None = headers
        self.config: Config = Config(config_path)
        self.vector_store: InMemoryVectorStore | None = vector_store
        self.graph: CompiledGraph = self.create_agent()

    def create_agent(self) -> CompiledGraph:
        """Create React Agent Graph."""

        # Retrieve LLM using get_llm with settings from config
        assert self.config.SMART_LLM_PROVIDER is not None, "smart_llm_provider is not set"
        assert self.config.SMART_LLM_MODEL is not None, "smart_llm_model is not set"
        assert isinstance(self.config.SMART_LLM_PROVIDER, str), (
            f"smart_llm_provider is not a str, was instead {type(self.config.SMART_LLM_PROVIDER).__name__}"
        )
        assert isinstance(self.config.SMART_LLM_MODEL, str), (
            f"smart_llm_model is not a str, was instead {type(self.config.SMART_LLM_MODEL).__name__}"
        )
        assert isinstance(self.config.llm_kwargs, dict), (
            f"llm_kwargs is not a dict, was instead {type(self.config.llm_kwargs).__name__}"
        )
        assert isinstance(self.config.EMBEDDING_KWARGS, dict), (
            f"embedding_kwargs is not a dict, was instead {type(self.config.EMBEDDING_KWARGS).__name__}"
        )
        assert isinstance(self.config.EMBEDDING_PROVIDER, str), (
            f"embedding_provider is not a str, was instead {type(self.config.EMBEDDING_PROVIDER).__name__}"
        )
        assert isinstance(self.config.EMBEDDING_MODEL, str), (
            f"embedding_model is not a str, was instead {type(self.config.EMBEDDING_MODEL).__name__}"
        )
        # Initialize LLM
        from gpt_researcher.utils.llm import get_llm_params
        params = get_llm_params(self.config.SMART_LLM_MODEL, temperature=0.35)

        provider: BaseChatModel = get_llm(
            llm_provider=self.config.SMART_LLM_PROVIDER,
            **params,
            **self.config.llm_kwargs,
        ).current_model

        # If vector_store is not initialized, process documents and add to vector_store
        assert self.config.EMBEDDING_PROVIDER is not None, "embedding_provider is not set"
        assert self.config.EMBEDDING_MODEL is not None, "embedding_model is not set"
        if not self.vector_store:
            documents: list[str] = self._process_document(self.report)
            self.chat_config: dict[str, Any] = {"configurable": {"thread_id": uuid.uuid4().hex}}
            self.embedding = Memory(
                self.config.EMBEDDING_PROVIDER,
                self.config.EMBEDDING_MODEL,
                **self.config.EMBEDDING_KWARGS,
            ).get_embeddings()
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)

        # Create the React Agent Graph with the configured provider
        graph: CompiledGraph = create_react_agent(
            provider,
            tools=[self.vector_store_tool(self.vector_store)],
            checkpointer=MemorySaver(),
        )

        return graph

    def vector_store_tool(
        self,
        vector_store: InMemoryVectorStore,
    ) -> BaseTool:
        """Create Vector Store Tool."""

        @tool
        def retrieve_info(query: str) -> list[str]:
            """Consult the report for relevant contexts whenever you don't know something."""
            retriever: VectorStoreRetriever = vector_store.as_retriever(k=4)
            return [page.page_content for page in retriever.invoke(query)]

        return retrieve_info

    def _process_document(
        self,
        report: str,
    ) -> list[str]:
        """Split Report into Chunks."""
        return RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        ).split_text(report)

    async def chat(
        self,
        message: str,
        websocket: WebSocket | None = None,
    ) -> str:
        """Chat with React Agent."""
        message = f"""You are GPT Researcher, a autonomous research agent created by an open source community at https://github.com/assafelovic/gpt-researcher, homepage: https://gptr.dev.
To learn more about GPT Researcher you can suggest to check out: https://docs.gptr.dev.

This is a chat message between the user and you: GPT Researcher.
The chat is about a research reports that you created. Answer based on the given context and report.
You must include citations to your answer based on the report.

Report: {self.report}
User Message: {message}"""
        inputs: dict[str, Any] = {"messages": [("user", message)]}
        cfg: RunnableConfig | Any = self.chat_config
        response: dict[str, Any] = await self.graph.ainvoke(inputs, config=cfg)
        last_message: Any = response["messages"][-1]
        ai_message: str = last_message.content
        if websocket is not None:  # fastapi
            await websocket.send_json(
                {
                    "type": "chat",
                    "content": ai_message,
                }
            )
        return ai_message

    def get_context(self) -> str:
        """return the current context of the chat."""
        return self.report
