from __future__ import annotations

import json
import logging

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import os

    from typing import TypedDict

    class EventData(TypedDict):
        data: dict[str, Any]
        timestamp: str
        type: str

    class ContentData(TypedDict):
        context: list[str]
        costs: float
        query: str
        report: str
        sources: list[str]

    class ResearchData(TypedDict):
        content: ContentData
        events: list[EventData]
        timestamp: str


class JSONResearchHandler:
    def __init__(
        self,
        json_file: os.PathLike | str,
    ):
        self.json_file: Path = Path(json_file)
        self.research_data: ResearchData | dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "events": [],
            "content": {
                "query": "",
                "sources": [],
                "context": [],
                "report": "",
                "costs": 0.0,
            },
        }

    def log_event(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        self.research_data["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": data,
            }
        )
        self._save_json()

    def update_content(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.research_data["content"][key] = value
        self._save_json()

    def _save_json(self):
        self.json_file.write_text(json.dumps(self.research_data, indent=2))


def setup_research_logging() -> tuple[str, str, logging.Logger, JSONResearchHandler]:
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Generate timestamp for log files
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create log file paths
    log_file: Path = logs_dir.joinpath(f"research_{timestamp}.log")
    json_file: Path = logs_dir.joinpath(f"research_{timestamp}.json")

    # Configure file handler for research logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Get research logger and configure it
    research_logger: logging.Logger = logging.getLogger("research")
    research_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicates
    research_logger.handlers.clear()

    # Add file handler
    research_logger.addHandler(file_handler)

    # Add stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    research_logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    research_logger.propagate = False

    # Create JSON handler
    json_handler = JSONResearchHandler(json_file)

    return str(log_file), str(json_file), research_logger, json_handler


def get_research_logger() -> logging.Logger:
    return logging.getLogger("research")
