from __future__ import annotations

import os

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gpt_researcher import GPTResearcher
from server.server_utils import CustomLogsHandler

if TYPE_CHECKING:
    from fastapi import WebSocket
    from gpt_researcher.utils.enum import ReportSource, ReportType, Tone


class BasicReporter:
    def __init__(
        self,
        query: str,
        report_type: str | ReportType,
        report_source: str | ReportSource,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone | None,
        config_path: os.PathLike | str,
        websocket: WebSocket | CustomLogsHandler,
        headers: dict[str, Any] | None = None,
        query_domains: list | None = None,
    ):
        self.query: str = query
        self.report_type: ReportType = ReportType(report_type.title()) if isinstance(report_type, str) else report_type
        self.report_source: ReportSource = ReportSource(report_source.title()) if isinstance(report_source, str) else report_source
        self.source_urls: list[str] = source_urls
        self.document_urls: list[str] = document_urls
        self.tone: Tone | None = Tone.Objective if tone is None else tone
        self.config_path: Path = Path(os.path.normpath(config_path)).absolute()
        self.websocket: WebSocket | CustomLogsHandler = websocket
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.query_domains: list[str] = [] if query_domains is None else query_domains

    async def run(self) -> str:
        # Initialize researcher
        researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone if isinstance(self.tone, Tone) else Tone(self.tone),
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers,
            query_domains=self.query_domains,
        )

        _research_context: str | list[str] = await researcher.conduct_research()
        report: str = await researcher.write_report()
        return report
