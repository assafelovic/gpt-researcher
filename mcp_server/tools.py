"""FastMCP tool wrappers around `gpt_researcher.agent.GPTResearcher`.

Tool names and stateful flow intentionally match the upstream
assafelovic/gptr-mcp project so MCP clients configured for that server can
point at the hosted HLT endpoint with minimal changes.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import FastMCP

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import Tone

logger = logging.getLogger(__name__)

STORE_TTL_SECONDS = 60 * 60
STORE_MAX_ITEMS = 32


@dataclass
class StoredResearch:
    """One in-memory research session for follow-up MCP tool calls."""

    researcher: GPTResearcher
    query: str
    context: Any
    sources: list[dict[str, Any]]
    source_urls: list[str]
    created_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)


_research_by_id: dict[str, StoredResearch] = {}
_resource_by_topic: dict[str, StoredResearch] = {}
_store_lock = asyncio.Lock()


def _resolve_tone(tone_str: str | None) -> Tone:
    if not tone_str:
        return Tone.Objective
    try:
        return Tone(tone_str)
    except ValueError:
        for tone in Tone:
            if tone.name.lower() == tone_str.lower() or tone.value.lower() == tone_str.lower():
                return tone
        logger.warning("Unknown tone %r; defaulting to Objective", tone_str)
        return Tone.Objective


def _success(data: dict[str, Any]) -> dict[str, Any]:
    return {"status": "success", **data}


def _error(message: str) -> dict[str, Any]:
    return {"status": "error", "message": message}


def _jsonable(value: Any) -> Any:
    """Return a JSON-compatible value without losing too much source context."""

    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [_jsonable(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _format_sources_for_response(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for source in sources:
        formatted.append(
            {
                "title": source.get("title", "Unknown"),
                "url": source.get("url", ""),
                "content_length": len(source.get("content", "") or ""),
            }
        )
    return formatted


def _format_context_with_sources(topic: str, context: Any, sources: list[dict[str, Any]]) -> str:
    context_text = context if isinstance(context, str) else json.dumps(_jsonable(context), indent=2)
    lines = [f"## Research: {topic}", "", context_text, "", "## Sources:"]
    for index, source in enumerate(sources, start=1):
        lines.append(f"{index}. {source.get('title', 'Unknown')}: {source.get('url', '')}")
    return "\n".join(lines)


def _result_count(results: Any) -> int:
    if results is None:
        return 0
    if isinstance(results, str):
        return 1 if results else 0
    try:
        return len(results)
    except TypeError:
        return 1


async def _prune_locked(now: float | None = None) -> None:
    now = now or time.time()
    expired_ids = [
        research_id
        for research_id, item in _research_by_id.items()
        if now - item.last_accessed_at > STORE_TTL_SECONDS
    ]
    for research_id in expired_ids:
        _research_by_id.pop(research_id, None)

    expired_topics = [
        topic
        for topic, item in _resource_by_topic.items()
        if now - item.last_accessed_at > STORE_TTL_SECONDS
    ]
    for topic in expired_topics:
        _resource_by_topic.pop(topic, None)

    while len(_research_by_id) > STORE_MAX_ITEMS:
        oldest_id = min(_research_by_id, key=lambda k: _research_by_id[k].last_accessed_at)
        _research_by_id.pop(oldest_id, None)

    while len(_resource_by_topic) > STORE_MAX_ITEMS:
        oldest_topic = min(_resource_by_topic, key=lambda k: _resource_by_topic[k].last_accessed_at)
        _resource_by_topic.pop(oldest_topic, None)


async def _store_research(research_id: str, item: StoredResearch, *, resource_topic: str | None = None) -> None:
    async with _store_lock:
        await _prune_locked()
        _research_by_id[research_id] = item
        if resource_topic:
            _resource_by_topic[resource_topic] = item


async def _get_research(research_id: str) -> StoredResearch | None:
    async with _store_lock:
        await _prune_locked()
        item = _research_by_id.get(research_id)
        if item:
            item.last_accessed_at = time.time()
        return item


async def _get_resource_topic(topic: str) -> StoredResearch | None:
    async with _store_lock:
        await _prune_locked()
        item = _resource_by_topic.get(topic)
        if item:
            item.last_accessed_at = time.time()
        return item


async def _conduct_research(
    query: str,
    *,
    report_type: str = "research_report",
    report_source: str = "web",
    tone: str = "Objective",
) -> StoredResearch:
    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        report_source=report_source,
        tone=_resolve_tone(tone),
    )
    await researcher.conduct_research()
    return StoredResearch(
        researcher=researcher,
        query=query,
        context=_jsonable(researcher.get_research_context()),
        sources=_jsonable(researcher.get_research_sources()),
        source_urls=list(researcher.get_source_urls()),
    )


def register_tools(mcp: FastMCP) -> None:
    """Register GPT Researcher MCP tools, resource, and prompt."""

    @mcp.resource("research://{topic}")
    async def research_resource(topic: str) -> str:
        """Return cached or newly generated research context for a topic."""

        cached = await _get_resource_topic(topic)
        if cached:
            return _format_context_with_sources(topic, cached.context, cached.sources)

        logger.info("Conducting resource research for topic=%r", topic)
        item = await _conduct_research(topic)
        research_id = str(uuid.uuid4())
        await _store_research(research_id, item, resource_topic=topic)
        return _format_context_with_sources(topic, item.context, item.sources)

    @mcp.tool()
    async def deep_research(
        query: str,
        report_type: str = "research_report",
        report_source: str = "web",
        tone: str = "Objective",
    ) -> dict[str, Any]:
        """Conduct deep research and return a research_id for follow-up calls."""

        research_id = str(uuid.uuid4())
        try:
            logger.info("Conducting deep research for research_id=%s query=%r", research_id, query)
            item = await _conduct_research(
                query,
                report_type=report_type,
                report_source=report_source,
                tone=tone,
            )
            await _store_research(research_id, item, resource_topic=query)
            return _success(
                {
                    "research_id": research_id,
                    "query": query,
                    "source_count": len(item.sources),
                    "context": item.context,
                    "sources": _format_sources_for_response(item.sources),
                    "source_urls": item.source_urls,
                }
            )
        except Exception as exc:
            logger.error("deep_research failed for query=%r: %s", query, exc, exc_info=True)
            return _error(str(exc))

    @mcp.tool()
    async def quick_search(
        query: str,
        summary: bool = True,
        domains: list[str] | None = None,
    ) -> dict[str, Any]:
        """Perform a fast web search without creating a research session."""

        search_id = str(uuid.uuid4())
        researcher = GPTResearcher(query=query, report_type="research_report")
        try:
            logger.info("Performing quick search for search_id=%s query=%r", search_id, query)
            results = await researcher.quick_search(
                query=query,
                query_domains=domains,
                aggregated_summary=summary,
            )
            return _success(
                {
                    "search_id": search_id,
                    "query": query,
                    "result_count": _result_count(results),
                    "search_results": _jsonable(results),
                }
            )
        except Exception as exc:
            logger.error("quick_search failed for query=%r: %s", query, exc, exc_info=True)
            return _error(str(exc))

    @mcp.tool()
    async def write_report(research_id: str, custom_prompt: str | None = None) -> dict[str, Any]:
        """Generate a report from a previous deep_research research_id."""

        item = await _get_research(research_id)
        if item is None:
            return _error("Research ID not found. Please conduct research first.")

        try:
            logger.info("Writing report for research_id=%s", research_id)
            report = await item.researcher.write_report(custom_prompt=custom_prompt or "")
            return _success(
                {
                    "research_id": research_id,
                    "report": report,
                    "source_count": len(item.sources),
                    "costs": item.researcher.get_costs(),
                }
            )
        except Exception as exc:
            logger.error("write_report failed for research_id=%s: %s", research_id, exc, exc_info=True)
            return _error(str(exc))

    @mcp.tool()
    async def get_research_sources(research_id: str) -> dict[str, Any]:
        """Return the sources used in a previous deep_research run."""

        item = await _get_research(research_id)
        if item is None:
            return _error("Research ID not found. Please conduct research first.")
        return _success(
            {
                "research_id": research_id,
                "sources": _format_sources_for_response(item.sources),
                "source_urls": item.source_urls,
            }
        )

    @mcp.tool()
    async def get_research_context(research_id: str) -> dict[str, Any]:
        """Return the full context from a previous deep_research run."""

        item = await _get_research(research_id)
        if item is None:
            return _error("Research ID not found. Please conduct research first.")
        return _success({"research_id": research_id, "context": item.context})

    @mcp.prompt()
    def research_query(topic: str, goal: str, report_format: str = "research_report") -> str:
        """Create an MCP prompt explaining how to use GPT Researcher tools."""

        return (
            f"Please research the following topic: {topic}\n\n"
            f"Goal: {goal}\n\n"
            "Use research://{topic} for direct context when appropriate, or call "
            "deep_research to get a research_id for follow-up calls. After deep_research, "
            f"use write_report with a custom prompt to generate a structured {report_format}."
        )

    logger.info(
        "Registered GPT Researcher MCP tools: deep_research, quick_search, "
        "write_report, get_research_sources, get_research_context"
    )
