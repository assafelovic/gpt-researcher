from __future__ import annotations

import uuid
from typing import Any

from fastapi import WebSocket
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool, tool
from langchain_community.vectorstores import InMemoryVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from gpt_researcher.config.config import Config
from gpt_researcher.memory import Memory
from gpt_researcher.utils.llm import get_llm


class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        config_path: str,
        headers: dict[str, str],
        vector_store: InMemoryVectorStore | None = None,
    ):
        self.report: str = report
        self.headers: dict[str, str] = headers
        self.config: Config = Config(config_path)
        self.vector_store: InMemoryVectorStore | None = vector_store
        self.graph: Any = self.create_agent()

    def create_agent(self):
        """Create React Agent Graph"""
        cfg = Config()

        # Retrieve LLM using get_llm with settings from config
        provider: Any = get_llm(
            llm_provider=cfg.smart_llm_provider,
            model=cfg.smart_llm_model,
            temperature=0.35,
            max_tokens=cfg.smart_token_limit,
            **self.config.llm_kwargs,
        ).llm

        # If vector_store is not initialized, process documents and add to vector_store
        if self.vector_store is None:
            documents: list[str] = self._process_document(self.report)
            self.chat_config: dict[str, dict[str, str]] = {
                "configurable": {"thread_id": str(uuid.uuid4())}
            }
            self.embedding: Any = Memory(
                cfg.embedding_provider,
                cfg.embedding_model,
                **cfg.embedding_kwargs,
            ).get_embeddings()
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)

        # Create the React Agent Graph with the configured provider
        graph = create_react_agent(
            provider,
            tools=[self.vector_store_tool(self.vector_store)],
            checkpointer=MemorySaver(),
        )

        return graph

    def vector_store_tool(
        self,
        vector_store: InMemoryVectorStore,
    ) -> Tool:
        """Create Vector Store Tool.

        Args:
            vector_store (InMemoryVectorStore): The vector store to use.

        Returns:
            Tool: The vector store tool.
        """

        @tool
        def retrieve_info(query: str) -> str:
            """Consult the report for relevant contexts whenever you don't know something."""
            retriever = vector_store.as_retriever(k=4)
            return retriever.invoke(query)

        return retrieve_info

    def _process_document(self, report: str) -> list[str]:
        """Split Report into Chunks"""
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        documents: list[str] = text_splitter.split_text(report)
        return documents

    async def chat(
        self,
        message: str,
        websocket: WebSocket | None = None,
    ) -> None:
        """Chat with React Agent.

        Args:
            message (str): The message to chat with.
            websocket (WebSocket | None): The websocket to send the response to.
        """
        message = f"""You are ResearchWizard, an autonomous research agent created by Boden Crouch (th3w1zard1).
To learn more about ResearchWizard you can suggest to contact Boden Crouch (th3w1zard1), your creator, directly.

This is a chat message between the user and you: ResearchWizard.
The chat is about a research report that you created. Answer based on the given context and report.
Do not start your response with 'Based on ...', use the report that was generated to infer an answer to the question/concern to the best of your ability.
You must include citations to your answer based on the report.

Report: {self.report}
User Message: {message}"""
        inputs: dict[str, list[tuple[str, str]]] = {"messages": [("user", message)]}
        response: dict[str, Any] = await self.graph.ainvoke(inputs, config=self.chat_config)
        ai_message: str = response["messages"][-1].content
        if websocket is not None:
            await websocket.send_json({"type": "chat", "content": ai_message})

    def get_context(self) -> str:
        """return the current context of the chat"""
        return self.report
