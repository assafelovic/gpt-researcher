"""FastMCP tool wrappers around `gpt_researcher.agent.GPTResearcher`.

Tool names and stateful flow intentionally match the upstream
assafelovic/gptr-mcp project so MCP clients configured for that server can
point at the hosted HLT endpoint with minimal changes.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from gpt_researcher import GPTResearcher
from gpt_researcher.research_run_store import get_outputs_dir, get_research_run_store
from gpt_researcher.utils.enum import Tone

logger = logging.getLogger(__name__)

STORE_TTL_SECONDS = 60 * 60
STORE_MAX_ITEMS = 32


@dataclass
class StoredResearch:
    """One in-memory research session for follow-up MCP tool calls."""

    researcher: GPTResearcher
    query: str
    report_type: str
    report_source: str
    tone: str
    context: Any
    sources: list[dict[str, Any]]
    source_urls: list[str]
    created_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)


_research_by_id: dict[str, StoredResearch] = {}
_resource_by_topic: dict[str, str] = {}
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
        if not isinstance(source, dict):
            formatted.append({"title": str(source), "url": "", "content_length": 0})
            continue
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
        if isinstance(source, dict):
            lines.append(f"{index}. {source.get('title', 'Unknown')}: {source.get('url', '')}")
        else:
            lines.append(f"{index}. {source}")
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
        for topic, research_id in _resource_by_topic.items()
        if research_id not in _research_by_id
        or now - _research_by_id[research_id].last_accessed_at > STORE_TTL_SECONDS
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
            _resource_by_topic[resource_topic] = research_id


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
        research_id = _resource_by_topic.get(topic)
        item = _research_by_id.get(research_id) if research_id else None
        if item:
            item.last_accessed_at = time.time()
        return item


def clear_hot_cache() -> None:
    _research_by_id.clear()
    _resource_by_topic.clear()


def _stored_research_from_run(run: dict[str, Any]) -> StoredResearch:
    researcher = GPTResearcher(
        query=run["query"],
        report_type=run.get("report_type") or "research_report",
        report_source=run.get("report_source") or "web",
        tone=_resolve_tone(run.get("tone")),
    )
    researcher.context = run.get("context") or []
    researcher.research_sources = run.get("sources") or []
    researcher.visited_urls = set(run.get("source_urls") or [])
    return StoredResearch(
        researcher=researcher,
        query=run["query"],
        report_type=run.get("report_type") or "research_report",
        report_source=run.get("report_source") or "web",
        tone=run.get("tone") or "Objective",
        context=run.get("context") or [],
        sources=run.get("sources") or [],
        source_urls=run.get("source_urls") or [],
    )


async def _get_research_or_persisted(research_id: str) -> tuple[StoredResearch | None, dict[str, Any] | None]:
    item = await _get_research(research_id)
    if item:
        return item, None

    run = get_research_run_store().get_run(research_id)
    if not run:
        return None, None
    if run.get("status") != "completed":
        return None, run

    item = _stored_research_from_run(run)
    await _store_research(research_id, item, resource_topic=run.get("resource_topic"))
    return item, run


def _safe_report_filename(research_id: str) -> str:
    return re.sub(r"[^\w\s-]", "", Path(research_id).name).strip() or str(uuid.uuid4())


async def _write_report_markdown(report: str, research_id: str) -> str:
    output_dir = get_outputs_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{_safe_report_filename(research_id)[:60]}.md"
    await asyncio.to_thread(report_path.write_text, report, "utf-8")
    return str(report_path)


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
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        context=_jsonable(researcher.get_research_context()),
        sources=_jsonable(researcher.get_research_sources()),
        source_urls=list(researcher.get_source_urls()),
    )


async def research_resource_tool(topic: str) -> str:
    cached = await _get_resource_topic(topic)
    if cached:
        return _format_context_with_sources(topic, cached.context, cached.sources)

    persisted = get_research_run_store().get_run_by_resource_topic(topic)
    if persisted and persisted.get("status") == "completed":
        item = _stored_research_from_run(persisted)
        await _store_research(persisted["research_id"], item, resource_topic=topic)
        return _format_context_with_sources(topic, item.context, item.sources)

    logger.info("Conducting resource research for topic=%r", topic)
    research_id = str(uuid.uuid4())
    store = get_research_run_store()
    store.create_run(
        research_id,
        query=topic,
        report_type="research_report",
        report_source="web",
        tone="Objective",
        status="running",
        resource_topic=topic,
    )
    try:
        item = await _conduct_research(topic)
        await _store_research(research_id, item, resource_topic=topic)
        store.complete_run(
            research_id,
            context=item.context,
            sources=item.sources,
            source_urls=item.source_urls,
            costs=item.researcher.get_costs(),
        )
        return _format_context_with_sources(topic, item.context, item.sources)
    except Exception as exc:
        store.fail_run(research_id, error_code="runtime_error", error_message=str(exc))
        raise


async def deep_research_tool(
    query: str,
    report_type: str = "research_report",
    report_source: str = "web",
    tone: str = "Objective",
) -> dict[str, Any]:
    research_id = str(uuid.uuid4())
    store = get_research_run_store()
    store.create_run(
        research_id,
        query=query,
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        status="running",
        resource_topic=query,
    )
    try:
        logger.info("Conducting deep research for research_id=%s query=%r", research_id, query)
        item = await _conduct_research(
            query,
            report_type=report_type,
            report_source=report_source,
            tone=tone,
        )
        await _store_research(research_id, item, resource_topic=query)
        store.complete_run(
            research_id,
            context=item.context,
            sources=item.sources,
            source_urls=item.source_urls,
            costs=item.researcher.get_costs(),
        )
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
        store.fail_run(research_id, error_code="runtime_error", error_message=str(exc))
        logger.error("deep_research failed for query=%r: %s", query, exc, exc_info=True)
        return _error(str(exc))


async def write_report_tool(research_id: str, custom_prompt: str | None = None) -> dict[str, Any]:
    item, persisted = await _get_research_or_persisted(research_id)
    if item is None:
        if persisted:
            return _error(f"Research ID is not completed; current status is {persisted.get('status')}.")
        return _error("Research ID not found. Please conduct research first.")

    try:
        logger.info("Writing report for research_id=%s", research_id)
        report = await item.researcher.write_report(custom_prompt=custom_prompt or "")
        md_path = await _write_report_markdown(report, research_id)
        item.context = _jsonable(item.researcher.get_research_context())
        item.sources = _jsonable(item.researcher.get_research_sources()) or item.sources
        item.source_urls = list(item.researcher.get_source_urls()) or item.source_urls
        get_research_run_store().complete_run(
            research_id,
            context=item.context,
            sources=item.sources,
            source_urls=item.source_urls,
            costs=item.researcher.get_costs(),
            report_path=md_path,
            md_path=md_path,
        )
        return _success(
            {
                "research_id": research_id,
                "report": report,
                "source_count": len(item.sources),
                "costs": item.researcher.get_costs(),
                "report_path": md_path,
                "md_path": md_path,
            }
        )
    except Exception as exc:
        logger.error("write_report failed for research_id=%s: %s", research_id, exc, exc_info=True)
        get_research_run_store().fail_run(research_id, error_code="runtime_error", error_message=str(exc))
        return _error(str(exc))


async def get_research_sources_tool(research_id: str) -> dict[str, Any]:
    item, persisted = await _get_research_or_persisted(research_id)
    if item is None:
        if persisted:
            return _error(f"Research ID is not completed; current status is {persisted.get('status')}.")
        return _error("Research ID not found. Please conduct research first.")
    return _success(
        {
            "research_id": research_id,
            "sources": _format_sources_for_response(item.sources),
            "source_urls": item.source_urls,
        }
    )


async def get_research_context_tool(research_id: str) -> dict[str, Any]:
    item, persisted = await _get_research_or_persisted(research_id)
    if item is None:
        if persisted:
            return _error(f"Research ID is not completed; current status is {persisted.get('status')}.")
        return _error("Research ID not found. Please conduct research first.")
    return _success({"research_id": research_id, "context": item.context})


def register_tools(mcp: FastMCP) -> None:
    """Register GPT Researcher MCP tools, resource, and prompt."""

    @mcp.resource("research://{topic}")
    async def research_resource(topic: str) -> str:
        """Return cached or newly generated research context for a topic."""
        return await research_resource_tool(topic)

    @mcp.tool()
    async def deep_research(
        query: str,
        report_type: str = "research_report",
        report_source: str = "web",
        tone: str = "Objective",
    ) -> dict[str, Any]:
        """Conduct deep research and return a research_id for follow-up calls."""

        return await deep_research_tool(query, report_type, report_source, tone)

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

        return await write_report_tool(research_id, custom_prompt)

    @mcp.tool()
    async def get_research_sources(research_id: str) -> dict[str, Any]:
        """Return the sources used in a previous deep_research run."""

        return await get_research_sources_tool(research_id)

    @mcp.tool()
    async def get_research_context(research_id: str) -> dict[str, Any]:
        """Return the full context from a previous deep_research run."""

        return await get_research_context_tool(research_id)

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
