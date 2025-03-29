from __future__ import annotations

import os

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, Tone

if TYPE_CHECKING:
    from fastapi import WebSocket

    from backend.server.server_utils import CustomLogsHandler


class BasicReport:
    def __init__(
        self,
        query: str,
        report_type: str | ReportType,
        report_source: str | ReportSource,
        config_path: os.PathLike | str | None = None,
        websocket: WebSocket | CustomLogsHandler | None = None,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        tone: Tone | str | None = Tone.Objective,
        report_format: str | ReportFormat | None = None,
        headers: dict[str, Any] | None = None,
        query_domains: list[str] | None = None,
        config: Config | None = None,
        **kwargs: Any,
    ):
        self.cfg: Config = Config(config_path) if config is None else config
        for key, value in kwargs.items():
            self.cfg.__setattr__(key, value)
        self.query: str = query
        self.report_type: ReportType = ReportType(report_type) if isinstance(report_type, str) else report_type
        self.report_source: ReportSource = ReportSource(report_source) if isinstance(report_source, str) else report_source
        self.report_format: ReportFormat = (
            ReportFormat(report_format) if isinstance(report_format, str) else report_format
            if isinstance(report_format, ReportFormat)
            else ReportFormat.APA
        )
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.tone: Tone = (
            Tone.Objective
            if tone is None
            else tone
            if isinstance(tone, Tone)
            else Tone.__members__[tone.capitalize()]
        )
        self.config_path: Path = Path(os.path.normpath(config_path)) if config_path is not None else Path.cwd()
        self.config: Config = Config.from_path(self.config_path) if config_path is not None else config if config is not None else Config()
        self.websocket: WebSocket | CustomLogsHandler | None = websocket
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.query_domains: list[str] = [] if query_domains is None else query_domains

    async def run(self) -> str:
        # Initialize researcher
        researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_format=self.report_format.value,
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone if isinstance(self.tone, Tone) else Tone(self.tone),
            websocket=self.websocket,
            headers=self.headers,
            query_domains=self.query_domains,
            config=self.config
        )

        try:
            _research_context: str | list[str] = await researcher.conduct_research()
            report: str = await researcher.write_report(
                existing_headers=[researcher.headers],
                relevant_written_contents=researcher.context,
                external_context=[],
            )
            return report
        except ValueError as e:
            if "No research data available" in str(e):
                return "Sorry, I was unable to gather any research data for your query. This could be due to network issues, API failures, or no relevant information being found. Please try again or rephrase your query."
            raise
