from fastapi import WebSocket
import uuid

from gpt_researcher.utils.llm import get_llm
from gpt_researcher.memory import Memory
from gpt_researcher.config.config import Config

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langchain_community.vectorstores import InMemoryVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool, tool

class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        config_path,
        headers,
        vector_store = None
    ):
        self.report = report
        self.headers = headers
        self.config = Config(config_path)
        self.vector_store = vector_store
        self.graph = self.create_agent()

    def create_agent(self):
        """Create React Agent Graph"""
        cfg = Config()

        # Retrieve LLM using get_llm with settings from config
        provider = get_llm(
            llm_provider=cfg.smart_llm_provider,
            model=cfg.smart_llm_model,
            temperature=0.35,
            max_tokens=cfg.smart_token_limit,
            **self.config.llm_kwargs
        ).llm

        # If vector_store is not initialized, process documents and add to vector_store
        if not self.vector_store:
            documents = self._process_document(self.report)
            self.chat_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            self.embedding = Memory(
                cfg.embedding_provider,
                cfg.embedding_model,
                **cfg.embedding_kwargs
            ).get_embeddings()
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)

        # Create the React Agent Graph with the configured provider
        graph = create_react_agent(
            provider,
            tools=[self.vector_store_tool(self.vector_store)],
            checkpointer=MemorySaver()
        )
        
        return graph
    
    def vector_store_tool(self, vector_store) -> Tool:
        """Create Vector Store Tool"""
        @tool 
        def retrieve_info(query):
            """
            Consult the report for relevant contexts whenever you don't know something
            """
            retriever = vector_store.as_retriever(k = 4)
            return retriever.invoke(query)
        return retrieve_info
        
    def _process_document(self, report):
        """Split Report into Chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        documents = text_splitter.split_text(report)
        return documents

    async def chat(self, message, websocket):
        """Chat with React Agent"""
        message = f"""
         You are GPT Researcher, a autonomous research agent created by an open source community at https://github.com/assafelovic/gpt-researcher, homepage: https://gptr.dev. 
         To learn more about GPT Researcher you can suggest to check out: https://docs.gptr.dev.
         
         This is a chat message between the user and you: GPT Researcher. 
         The chat is about a research reports that you created. Answer based on the given context and report.
         You must include citations to your answer based on the report.
         
         Report: {self.report}
         User Message: {message}
        """
        inputs = {"messages": [("user", message)]}
        response = await self.graph.ainvoke(inputs, config=self.chat_config)
        ai_message = response["messages"][-1].content
        if websocket is not None:
            await websocket.send_json({"type": "chat", "content": ai_message})

    def get_context(self):
        """return the current context of the chat"""
        return self.report
