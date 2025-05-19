from fastapi import WebSocket
from typing import Any

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import Tone, ReportType, ReportSource


class BasicReport:
    def __init__(
        self,
        query: str,
        report_type: ReportType | str,
        report_source: ReportSource | str,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone | str,
        config_path: str,
        websocket: WebSocket,
        headers: dict[str, Any] | None = None
    ):
        self.query: str = query
        self.report_type: ReportType | str = report_type
        self.report_source: ReportSource | str = report_source
        self.source_urls: list[str] = source_urls
        self.document_urls: list[str] = document_urls
        self.tone: Tone | str = tone
        self.config_path: str = config_path
        self.websocket: WebSocket = websocket
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.researcher: GPTResearcher | None = None

    async def run(self) -> str:
        # Initialize researcher
        self.researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone,
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers
        )

        await self.researcher.conduct_research()
        report: str = await self.researcher.write_report()
        return report
