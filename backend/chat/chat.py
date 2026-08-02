import logging
import os
import uuid
import json
from fastapi import WebSocket
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore
from gpt_researcher.memory import Memory
from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.tools import create_chat_completion_with_tools, create_search_tool
try:
    from tavily import TavilyClient
except ImportError:  # optional dependency for chat web search
    TavilyClient = None
from datetime import datetime

# Setup logging
# Get logger instance
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ]
)

# Note: LLM client is now handled through GPT Researcher's unified LLM system
# This supports all configured providers (OpenAI, Google Gemini, Anthropic, etc.)

def get_tools():
    """Define tools for LLM function calling (primarily for OpenAI-compatible providers)"""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "quick_search",
                "description": "Search for current events or online information when you need new knowledge that doesn't exist in the current context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    return tools

class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        config_path="default",
        headers=None,
        vector_store=None
    ):
        self.report = report
        self.headers = headers
        self.config = Config(config_path)
        self.vector_store = vector_store
        self.retriever = None
        self.search_metadata = None
        
        # Initialize Tavily client (optional - only if API key is available)
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if tavily_api_key and TavilyClient is not None:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
        else:
            self.tavily_client = None
            if TavilyClient is None:
                logger.warning("tavily package not installed - web search in chat will be disabled")
            else:
                logger.warning("TAVILY_API_KEY not set - web search in chat will be disabled")
        
        # Process document and create vector store if not provided
        if not self.vector_store and self.report:
            self._setup_vector_store()
        elif self.vector_store is not None and self.retriever is None:
            # Allow callers to inject a store; build a retriever with supported kwargs.
            try:
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})
            except TypeError:
                self.retriever = self.vector_store.as_retriever()
    
    def _setup_vector_store(self):
        """Setup vector store for document retrieval"""
        # Process document into chunks
        documents = self._process_document(self.report)
        if not documents:
            return
        
        # Create unique thread ID
        self.thread_id = str(uuid.uuid4())
        
        # Setup embeddings and vector store using the agent config_path.
        # Embedding construction can fail eagerly (e.g. OpenAI embeddings raise
        # at init when OPENAI_API_KEY is unset), so fall back to no-RAG / full
        # report mode instead of leaving chat broken for that message.
        cfg = self.config
        try:
            self.embedding = Memory(
                cfg.embedding_provider,
                cfg.embedding_model,
                **cfg.embedding_kwargs
            ).get_embeddings()

            # Create vector store and retriever
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)
            try:
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})
            except TypeError:
                # Older langchain APIs accepted k= directly; prefer kwargs form.
                self.retriever = self.vector_store.as_retriever(k=4)
        except Exception as exc:  # noqa: BLE001 - embeddings must not break chat
            logger.warning(
                f"Vector store setup failed, using full report (no RAG): {exc}"
            )
            self.embedding = None
            self.vector_store = None
            self.retriever = None
        
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

    def quick_search(self, query):
        """Perform a web search for current information using Tavily"""
        try:
            # Check if Tavily client is available
            if self.tavily_client is None:
                logger.warning(f"Tavily client not available, skipping web search for: {query}")
                self.search_metadata = {
                    "query": query,
                    "sources": [],
                    "error": "Web search is disabled - TAVILY_API_KEY not configured"
                }
                return {
                    "error": "Web search is disabled - TAVILY_API_KEY not configured",
                    "results": []
                }
            
            logger.info(f"Performing web search for: {query}")
            results = self.tavily_client.search(query=query, max_results=5)
            
            # Store search metadata for frontend
            self.search_metadata = {
                "query": query,
                "sources": [
                    {"title": result.get("title", ""), 
                     "url": result.get("url", ""),
                     "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")}
                    for result in results.get("results", [])
                ]
            }
            
            return results
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "results": []
            }


    async def process_chat_completion(self, messages: List[Dict[str, str]]):
        """Process chat completion using configured LLM provider with tool calling support"""
        # Create a search tool using the utility function
        search_tool = create_search_tool(self.quick_search)
        
        # Use the tool-enabled chat completion utility
        response, tool_calls_metadata = await create_chat_completion_with_tools(
            messages=messages,
            tools=[search_tool],
            model=self.config.smart_llm_model,
            llm_provider=self.config.smart_llm_provider,
            llm_kwargs=self.config.llm_kwargs,
        )
        
        # Process metadata to match the expected format for the chat system
        processed_metadata = []
        for metadata in tool_calls_metadata:
            if metadata.get("tool") == "search_tool":
                # Extract query from args
                query = metadata.get("args", {}).get("query", "")
                
                # Trigger search again to get metadata (the search was already executed by LangChain)
                if query:
                    self.quick_search(query)  # This populates self.search_metadata
                    
                processed_metadata.append({
                    "tool": "quick_search",
                    "query": query,
                    "search_metadata": self.search_metadata
                })
        
        return response, processed_metadata



    def _retrieve_context(self, user_message: str) -> str:
        """Return top retrieved report chunks for the latest user message.

        Falls back to the full report when retrieval is unavailable so chat stays
        usable offline / without embeddings.
        """
        if not self.retriever or not user_message:
            return self.report or ""
        try:
            docs = self.retriever.invoke(user_message)
        except Exception as exc:  # noqa: BLE001 - retrieval must not break chat
            logger.warning(f"Report retrieval failed, using full report: {exc}")
            return self.report or ""
        chunks = []
        for doc in docs or []:
            content = getattr(doc, "page_content", None)
            if content is None and isinstance(doc, dict):
                content = doc.get("page_content") or doc.get("content")
            if content:
                chunks.append(str(content))
        if not chunks:
            return self.report or ""
        return "\n\n".join(chunks)

    async def chat(self, messages, websocket=None):
        """Chat with configured LLM provider (supports OpenAI, Google Gemini, Anthropic, etc.)
        
        Args:
            messages: List of chat messages with role and content
            websocket: Optional websocket for streaming responses
        
        Returns:
            tuple: (str: The AI response message, dict: metadata about tool usage)
        """
        try:
            
            # Prefer retrieved report slices over stuffing the entire report each turn
            last_user = ""
            for msg in reversed(messages or []):
                if isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content"):
                    last_user = str(msg.get("content"))
                    break
            report_context = self._retrieve_context(last_user)

            # Format system prompt with the report context
            system_prompt = f"""
            You are GPT Researcher, an autonomous research agent created by an open source community at https://github.com/assafelovic/gpt-researcher, homepage: https://gptr.dev. 
            To learn more about GPT Researcher you can suggest to check out: https://docs.gptr.dev.
            
            This is a chat about a research report that you created. Answer based on the given context and report.
            You must include citations to your answer based on the report.
            
            You may use the quick_search tool when the user asks about information that might require current data 
            not found in the report, such as recent events, updated statistics, or news. If there's no report available,
            you can use the quick_search tool to find information online.
            
            You must respond in markdown format. You must make it readable with paragraphs, tables, etc when possible. 
            Remember that you're answering in a chat not a report.
            
            Assume the current time is: {datetime.now()}.
            
            Report: {report_context}
            
            """
            
            # Format message history for OpenAI input
            formatted_messages = []
            
            # Add system message first
            formatted_messages.append({
                "role": "system", 
                "content": system_prompt
            })
            
            # Add user/assistant message history - filter out non-essential fields
            for msg in messages:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                else:
                    logger.warning(f"Skipping message with missing role or content: {msg}")
            
            # Process the chat using configured LLM provider
            ai_message, tool_calls_metadata = await self.process_chat_completion(formatted_messages)
            
            # Provide fallback response if message is empty
            if not ai_message:
                logger.warning("No AI message content found in response, using fallback message")
                ai_message = "I apologize, but I couldn't generate a proper response. Please try asking your question again."
            
            logger.info(f"Generated response: {ai_message[:100]}..." if len(ai_message) > 100 else f"Generated response: {ai_message}")
            
            # Return both the message and any metadata about tools used
            return ai_message, tool_calls_metadata
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise

    def get_context(self):
        """return the current context of the chat"""
        return self.report
