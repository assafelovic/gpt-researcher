from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gpt_researcher import GPTResearcher

if TYPE_CHECKING:
    from fastapi import WebSocket
    from gpt_researcher.utils.schemas import Tone


class BasicReporter:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls: list[str],
        document_urls: list[str],
        tone: Tone | None,
        config_path: os.PathLike | str,
        websocket: WebSocket,
        headers: dict[str, Any] | None = None,
    ):
        self.query: str = query
        self.report_type: str = report_type
        self.report_source: str = report_source
        self.source_urls: list[str] = source_urls
        self.document_urls: list[str] = document_urls
        self.tone: Tone | None = tone
        self.config_path: Path = Path(os.path.normpath(config_path)).absolute()
        self.websocket: WebSocket = websocket
        self.headers: dict[str, Any] = {} if headers is None else headers

    async def run(self):
        # Initialize researcher
        researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone,
            config=self.config_path,
            websocket=self.websocket,
            headers=self.headers,
        )

        _research_context = await researcher.conduct_research()
        report: str = await researcher.write_report()
        return report
