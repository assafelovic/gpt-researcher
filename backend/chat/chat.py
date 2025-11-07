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
from tavily import TavilyClient
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
        
        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
        
        # Process document and create vector store if not provided
        if not self.vector_store and False:
            self._setup_vector_store()
    
    def _setup_vector_store(self):
        """Setup vector store for document retrieval"""
        # Process document into chunks
        documents = self._process_document(self.report)
        
        # Create unique thread ID
        self.thread_id = str(uuid.uuid4())
        
        # Setup embeddings and vector store
        cfg = Config()
        self.embedding = Memory(
            cfg.embedding_provider,
            cfg.embedding_model,
            **cfg.embedding_kwargs
        ).get_embeddings()
        
        # Create vector store and retriever
        self.vector_store = InMemoryVectorStore(self.embedding)
        self.vector_store.add_texts(documents)
        self.retriever = self.vector_store.as_retriever(k=4)
        
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


    async def chat(self, messages, websocket=None):
        """Chat with configured LLM provider (supports OpenAI, Google Gemini, Anthropic, etc.)
        
        Args:
            messages: List of chat messages with role and content
            websocket: Optional websocket for streaming responses
        
        Returns:
            tuple: (str: The AI response message, dict: metadata about tool usage)
        """
        try:
            
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
            
            Report: {self.report}
            
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
                if 'role' in msg and 'content' in msg:
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
