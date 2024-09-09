from fastapi import WebSocket
import uuid

from gpt_researcher.utils.llm import get_llm
from gpt_researcher.memory import Memory
from gpt_researcher.config import Config

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langchain_community.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import Tool, tool

class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        websocket: WebSocket,
        config_path,
        headers, 
    ):
        self.report = report
        self.websocket = websocket
        self.headers = headers
        self.config = Config(config_path)
        self.graph = self.create_agent()

    def create_agent(self):
        documents = self._process_document(self.report)
        provider = get_llm(self.config.llm_provider, model=self.config.smart_llm_model, temperature=self.config.temperature, max_tokens=self.config.smart_token_limit, **self.config.llm_kwargs).llm
        self.chat_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self.embedding = Memory(self.config.embedding_provider, self.headers).get_embeddings()
        vector_store = InMemoryVectorStore(self.embedding)
        vector_store.add_texts(documents)
        graph = create_react_agent(provider, tools=[self.vector_store_tool(vector_store)], checkpointer=MemorySaver())
        return graph
    
    def vector_store_tool(self, vector_store) -> Tool:
        @tool 
        def retrieve_info(query):
            """
            Consult the report for relevant contexts whenever you don't know something
            """
            retriever = vector_store.as_retriever(k = 4)
            return retriever.invoke(query)
        return retrieve_info
        
    def _process_document(self, report):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        documents = text_splitter.split_text(report)
        return documents

    async def chat(self, message):
        inputs = {"messages": [("user", message)]}
        response = await self.graph.ainvoke(inputs, config=self.chat_config)
        ai_message = (response["messages"][-1].content)
        print(ai_message)
        if self.websocket is not None:
            await self.websocket.send_json({"type": "chat", "content": ai_message})
