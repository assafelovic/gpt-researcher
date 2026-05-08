import logging
import os
import asyncio
import re
from typing import List, Dict, Any

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.retrievers import Duckduckgo

try:
    from tavily import TavilyClient
except ImportError:  # pragma: no cover - optional dependency.
    TavilyClient = None

# Setup logging
# Get logger instance
logger = logging.getLogger(__name__)

CHAT_REQUEST_TIMEOUT = float(os.getenv("CHAT_REQUEST_TIMEOUT", "6"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "800"))
CHAT_REPORT_CONTEXT_CHARS = int(os.getenv("CHAT_REPORT_CONTEXT_CHARS", "12000"))

_GREETING_RE = re.compile(
    r"^(hi|hello|hey|hallo|moin|yo|good morning|good afternoon|good evening|thanks|thank you|danke)([!.?\s]*)$",
    re.IGNORECASE,
)
_SEARCH_HINTS = (
    "latest",
    "recent",
    "current",
    "today",
    "tonight",
    "right now",
    "now",
    "news",
    "breaking",
    "updated",
    "update",
    "live",
    "stock",
    "price",
    "weather",
    "forecast",
    "search the web",
    "search online",
    "look up",
    "browse",
    "internet",
    "web",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Only log to console
    ]
)

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
        
        # Initialize Tavily client (optional - only if API key and package are available)
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if tavily_api_key and TavilyClient is not None:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
        else:
            self.tavily_client = None
            logger.warning("Tavily is unavailable - chat web search will use DuckDuckGo fallback")

    @staticmethod
    def _latest_user_message(messages: List[Dict[str, str]]) -> str:
        for message in reversed(messages or []):
            if message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str):
                    cleaned = content.strip()
                    if cleaned:
                        return cleaned
        return ""

    @staticmethod
    def _is_simple_greeting(message: str) -> bool:
        if not message:
            return False
        if len(message.split()) > 4:
            return False
        return bool(_GREETING_RE.match(message.strip()))

    @staticmethod
    def _should_use_search(message: str) -> bool:
        if not message:
            return False
        lowered = message.lower()
        return any(hint in lowered for hint in _SEARCH_HINTS)

    @staticmethod
    def _is_summary_request(message: str) -> bool:
        if not message:
            return False
        lowered = message.lower()
        return any(
            phrase in lowered
            for phrase in (
                "summarize",
                "summary",
                "tl;dr",
                "tldr",
                "one sentence",
                "in one sentence",
                "brief summary",
                "short summary",
            )
        )

    @staticmethod
    def _extract_report_summary(report: str) -> str:
        if not report:
            return ""

        text = re.sub(r"(?m)^#+\s*", "", report).strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        source = paragraphs[0] if paragraphs else text
        first_sentence = re.split(r"(?<=[.!?])\s+", source, maxsplit=1)[0].strip()
        if not first_sentence:
            first_sentence = source[:240].strip()
        if not first_sentence.endswith((".", "!", "?")):
            first_sentence += "."
        return f"According to the report, {first_sentence}"

    @staticmethod
    def _build_report_answer(query: str, report: str) -> str:
        if not report:
            return ""

        query_tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", (query or "").lower())
            if len(token) > 2
        }
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", report)
            if sentence.strip()
        ]
        if not sentences:
            return ""

        scored_sentences = []
        for sentence in sentences:
            sentence_tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            score = len(query_tokens & sentence_tokens)
            scored_sentences.append((score, sentence))

        scored_sentences.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        best_sentences = [sentence for score, sentence in scored_sentences[:2] if score > 0]
        if not best_sentences:
            best_sentences = sentences[:2]

        answer = " ".join(best_sentences).strip()
        if not answer.endswith((".", "!", "?")):
            answer += "."
        return f"Based on the report, {answer}"

    @staticmethod
    def _build_search_answer(query: str, search_metadata: Dict[str, Any] | None) -> str:
        if not search_metadata:
            return f"I couldn't find live search results for {query}."

        sources = search_metadata.get("sources") or []
        if not sources:
            error = search_metadata.get("error")
            if error:
                return f"I couldn't complete the live search for {query}: {error}"
            return f"I couldn't find live search results for {query}."

        lines = [f"Here's what I found about {query.strip()}:"]
        for source in sources[:3]:
            title = source.get("title") or "Source"
            url = source.get("url") or ""
            content = (source.get("content") or "").strip()
            if content:
                lines.append(f"* **{title}**: {content}")
            else:
                lines.append(f"* **{title}**")
            if url:
                lines.append(f"  Source: {url}")
        return "\n".join(lines)

    @staticmethod
    def _sanitize_ai_message(message: str) -> str:
        if not message:
            return message
        cleaned = re.sub(r"/\*\s*content-m:.*?\*/", "", message, flags=re.DOTALL)
        return cleaned.strip()

    def _build_system_prompt(self) -> str:
        report_context = (self.report or "").strip()
        if report_context and len(report_context) > CHAT_REPORT_CONTEXT_CHARS:
            report_context = (
                report_context[:CHAT_REPORT_CONTEXT_CHARS]
                + "\n\n[Report context truncated for chat.]"
            )

        prompt_parts = [
            "You are GPT Researcher chat assistant.",
            "Answer in markdown. Keep it concise, direct, and useful.",
        ]

        if report_context:
            prompt_parts.append(
                "Use the report context below as the primary source for report questions."
            )
            prompt_parts.append(
                "If the answer is not in the report, say that clearly instead of inventing details."
            )
            prompt_parts.append(f"Report context:\n{report_context}")
        else:
            prompt_parts.append(
                "No report context was provided."
            )

        return "\n\n".join(prompt_parts)

    def quick_search(self, query):
        """Perform a web search for current information."""
        try:
            # Check if Tavily client is available
            if self.tavily_client is None:
                logger.info(f"Using DuckDuckGo fallback search for: {query}")
                results = Duckduckgo(query).search(max_results=5)
                normalized_results = self._normalize_search_results(results)
                self.search_metadata = {
                    "query": query,
                    "sources": normalized_results,
                }
                return {"results": normalized_results}

            logger.info(f"Performing web search for: {query}")
            results = self.tavily_client.search(query=query, max_results=5)
            normalized_results = self._normalize_search_results(results.get("results", []))
            
            # Store search metadata for frontend
            self.search_metadata = {
                "query": query,
                "sources": normalized_results,
            }
            
            return {"results": normalized_results}
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}", exc_info=True)
            self.search_metadata = {
                "query": query,
                "sources": [],
                "error": str(e),
            }
            return {
                "error": str(e),
                "results": []
            }

    @staticmethod
    def _normalize_search_results(results):
        normalized = []
        for result in results[:5]:
            title = result.get("title") or result.get("name") or ""
            url = result.get("url") or result.get("href") or ""
            content = result.get("content") or result.get("body") or ""
            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "content": content[:300],
                }
            )
        return normalized


    async def process_chat_completion(self, messages: List[Dict[str, str]]):
        """Process chat completion using configured LLM provider."""
        llm_kwargs = dict(self.config.llm_kwargs or {})
        llm_kwargs.setdefault("timeout", CHAT_REQUEST_TIMEOUT)
        model = self.config.smart_llm_model or self.config.fast_llm_model
        provider = self.config.smart_llm_provider or self.config.fast_llm_provider
        try:
            response = await asyncio.wait_for(
                create_chat_completion(
                    messages=messages,
                    model=model,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.smart_token_limit, CHAT_MAX_TOKENS),
                    llm_provider=provider,
                    llm_kwargs=llm_kwargs,
                ),
                timeout=CHAT_REQUEST_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning("Chat completion timed out")
            if self.report:
                fallback = self._build_report_answer(
                    self._latest_user_message(messages),
                    self.report,
                )
                if fallback:
                    return fallback, []
            return (
                "I couldn't generate a response quickly enough. Please narrow the question and try again.",
                [],
            )
        except Exception as exc:
            logger.error(f"Chat completion failed: {exc}", exc_info=True)
            if self.report:
                fallback = self._build_report_answer(
                    self._latest_user_message(messages),
                    self.report,
                )
                if fallback:
                    return fallback, []
            return (
                "I couldn't generate a response for that message right now. Please try again.",
                [],
            )

        return response, []


    async def chat(self, messages, websocket=None):
        """Chat with configured LLM provider (supports OpenAI, Google Gemini, Anthropic, etc.)
        
        Args:
            messages: List of chat messages with role and content
            websocket: Optional websocket for streaming responses
        
        Returns:
            tuple: (str: The AI response message, dict: metadata about tool usage)
        """
        try:
            self.search_metadata = None
            latest_user_message = self._latest_user_message(messages)
            use_search = self._should_use_search(latest_user_message)

            if self._is_simple_greeting(latest_user_message):
                if self.report:
                    return (
                        "Hello. Ask me about the report or a current topic, and I will answer directly.",
                        [],
                    )
                return ("Hello. What would you like to research?", [])

            if self.report and not use_search and self._is_summary_request(latest_user_message):
                return (self._extract_report_summary(self.report), [])

            tool_calls_metadata = []
            if use_search:
                self.quick_search(latest_user_message)
                tool_calls_metadata = [{
                    "tool": "quick_search",
                    "query": latest_user_message,
                    "search_metadata": self.search_metadata,
                }]
                return (
                    self._build_search_answer(latest_user_message, self.search_metadata),
                    tool_calls_metadata,
                )

            system_prompt = self._build_system_prompt()
            
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
            ai_message, tool_calls_metadata = await self.process_chat_completion(
                formatted_messages,
            )
            ai_message = self._sanitize_ai_message(ai_message)
            
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
