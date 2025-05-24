from __future__ import annotations

from typing import Any

from fastapi import WebSocket
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone


class BasicReport:
    def __init__(
        self,
        query: str,
        query_domains: list[str],
        report_type: ReportType | str,
        report_source: ReportSource | str,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone | str,
        config_path: str,
        websocket: WebSocket,
        headers: dict[str, Any] | None = None,
    ):
        self.query: str = query
        self.query_domains: list[str] = query_domains
        self.report_type: ReportType | str = report_type
        self.report_source: ReportSource | str = report_source
        self.source_urls: list[str] = source_urls
        self.document_urls: list[str] = document_urls
        self.tone: Tone | str = tone
        self.config_path: str = config_path
        self.websocket: WebSocket = websocket
        self.headers: dict[str, Any] = {} if headers is None else headers

        # Initialize researcher
        self.gpt_researcher = GPTResearcher(
            query=self.query,
            query_domains=self.query_domains,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone,
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers,
        )

    async def run(self) -> str:
        await self.gpt_researcher.conduct_research()
        report: str = await self.gpt_researcher.write_report()
        return report
