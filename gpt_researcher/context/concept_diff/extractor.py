"""Industry-Grade LLM Fact Extraction Pipeline for GPT Researcher Concept-Diff Ingestion.

Performs structured LLM-driven fact, metric, and entity triplet extraction with
built-in rate-limit protection (concurrency throttling + exponential backoff retry)
and comprehensive error diagnostics.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import json_repair
from langchain_core.utils.json import parse_json_markdown

from gpt_researcher.utils.llm import create_chat_completion
from .knowledge_graph import FactAssertion

logger = logging.getLogger(__name__)


class FactExtractor:
    """Production-grade LLM structured fact extractor with rate-limit and error safeguards."""

    CLEAN_HTML_TAGS = re.compile(r"<script.*?>.*?</script>|<style.*?>.*?</style>|<.*?>", re.DOTALL | re.IGNORECASE)

    def __init__(
        self,
        llm_model: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        cost_callback: Optional[Callable[[float], None]] = None,
        max_concurrency: int = 4,
        max_retries: int = 3,
        retry_base_delay: float = 1.5,
    ) -> None:
        """Initialize the FactExtractor.

        Args:
            llm_model: The LLM model to use (e.g. 'gemini-2.5-flash', 'gpt-4o-mini').
            llm_provider: The provider name ('google', 'openai', etc.).
            llm_kwargs: Extra provider keyword arguments.
            cost_callback: Callback function to record token costs.
            max_concurrency: Maximum simultaneous LLM extraction requests to prevent rate-limit spikes.
            max_retries: Number of retry attempts on rate-limit (429) or transient errors.
            retry_base_delay: Base delay in seconds for exponential backoff.
        """
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.llm_kwargs = llm_kwargs or {}
        self.cost_callback = cost_callback
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._semaphore = asyncio.Semaphore(max_concurrency)

    def clean_text(self, text: str) -> str:
        """Strip raw HTML markup and collapse whitespace."""
        if not text:
            return ""
        cleaned = self.CLEAN_HTML_TAGS.sub(" ", text)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _diagnose_error(self, error: Exception) -> str:
        """Analyze an exception and produce an actionable diagnostic message."""
        err_msg = str(error).lower()
        if "429" in err_msg or "rate limit" in err_msg or "resource_exhausted" in err_msg:
            return f"Rate limit / Quota threshold reached for provider '{self.llm_provider}' (Model: {self.llm_model}). Throttling and retrying."
        if "401" in err_msg or "unauthorized" in err_msg or "invalid api key" in err_msg or "authentication" in err_msg:
            return f"Authentication failed: Invalid API key configured for provider '{self.llm_provider}'."
        if "404" in err_msg or "not found" in err_msg:
            return f"Model '{self.llm_model}' not found or unsupported by provider '{self.llm_provider}'."
        if "context length" in err_msg or "maximum context" in err_msg or "tokens" in err_msg:
            return f"Token limit exceeded for model '{self.llm_model}'."
        return f"LLM provider error ({type(error).__name__}): {error}"

    async def extract_facts(
        self,
        raw_text: str,
        source_url: str = "",
        source_title: str = "",
        max_chars: int = 12000,
    ) -> List[FactAssertion]:
        """Extract atomic facts, metrics, and assertions from raw web text.

        Args:
            raw_text: The scraped text content.
            source_url: URL of the origin page.
            source_title: Title of the origin page.
            max_chars: Maximum characters to inspect from the document.

        Returns:
            A list of extracted FactAssertion instances.

        Raises:
            ValueError: If no LLM model is configured.
        """
        if not self.llm_model:
            logger.error("Concept-Diff Extraction Error: No LLM model configured for FactExtractor.")
            raise ValueError(
                "FactExtractor requires an active LLM model. Please configure FAST_LLM or SMART_LLM in your settings."
            )

        if not raw_text or not raw_text.strip():
            return []

        text_snippet = self.clean_text(raw_text[:max_chars])
        if len(text_snippet) < 30:
            return []

        system_prompt = (
            "You are a high-precision factual knowledge extraction engine for automated research synthesis.\n"
            "Extract all unique, high-signal atomic facts, metrics, breakthrough claims, dates, prices, and statistics.\n"
            "Strictly ignore introductory background fluff, company boilerplate history, navigation, or generic definitions.\n"
            "Output ONLY a valid JSON list of objects matching this exact schema:\n"
            "[\n"
            "  {\n"
            '    "subject": "Entity or concept name",\n'
            '    "predicate": "Action, verb, property, or relationship",\n'
            '    "object_val": "Specific metric, claim, target, or value",\n'
            '    "is_numeric": true/false,\n'
            '    "context_snippet": "Exact sentence snippet from text containing this fact"\n'
            "  }\n"
            "]"
        )

        user_prompt = (
            f"SOURCE TITLE: {source_title}\n"
            f"SOURCE URL: {source_url}\n"
            f"TEXT CONTENT:\n{text_snippet}"
        )

        # Concurrency-controlled execution with exponential backoff for rate limits
        async with self._semaphore:
            last_error: Optional[Exception] = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await create_chat_completion(
                        model=self.llm_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.0,
                        max_tokens=2000,
                        llm_provider=self.llm_provider,
                        llm_kwargs=self.llm_kwargs,
                        cost_callback=self.cost_callback,
                    )

                    parsed_json = parse_json_markdown(response, parser=json_repair.loads)
                    if not isinstance(parsed_json, list):
                        logger.warning(
                            f"Structured extraction on '{source_url}' returned non-list JSON ({type(parsed_json).__name__})."
                        )
                        return []

                    assertions: List[FactAssertion] = []
                    for item in parsed_json:
                        if isinstance(item, dict) and item.get("subject") and item.get("object_val"):
                            assertions.append(
                                FactAssertion(
                                    subject=str(item.get("subject", "")).strip(),
                                    predicate=str(item.get("predicate", "states")).strip(),
                                    object_val=str(item.get("object_val", "")).strip(),
                                    is_numeric=bool(item.get("is_numeric", False)),
                                    source_url=source_url,
                                    source_title=source_title,
                                    context_snippet=str(item.get("context_snippet", "")).strip(),
                                )
                            )
                    return assertions

                except Exception as e:
                    last_error = e
                    diag_msg = self._diagnose_error(e)
                    logger.warning(
                        f"Concept-Diff extraction attempt {attempt}/{self.max_retries} failed for '{source_url}': {diag_msg}"
                    )

                    if attempt < self.max_retries:
                        backoff = self.retry_base_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(backoff)

            # If all retries fail, log the persistent issue
            logger.error(
                f"Concept-Diff Extraction failed permanently for '{source_url}'. Final Diagnostic: {self._diagnose_error(last_error)}"
            )
            return []
