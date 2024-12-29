"""Controller for managing file operations."""

from __future__ import annotations

import json
import logging

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import toga.platform

if TYPE_CHECKING:
    from toga.window import Window

logger = logging.getLogger(__name__)


class FileController:
    """Controls file operations."""

    def __init__(self, window: Window):
        self.window: Window = window

    async def copy_to_clipboard(self, content: str) -> bool:
        """Copy content to clipboard.

        Args:
            content: Text content to copy

        Returns:
            True if successful, False otherwise
        """
        try:
            clipboard = toga.platform.get_platform_factory().Clipboard()
            clipboard.set_text(content)
            return True
        except Exception:
            logger.exception("Error copying to clipboard")
            return False

    async def save_markdown(self, content: str) -> Path | None:
        """Save content as Markdown file.

        Args:
            content: Text content to save

        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            save_path = await self.window.save_file_dialog(
                "Save Markdown File",
                suggested_filename="research_report.md",
                file_types=["md"],
            )
            if save_path and str(save_path).strip():
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return Path(save_path)
            return None
        except Exception:
            logger.exception("Error saving markdown file")
            return None

    async def save_pdf(self, content: str) -> Path | None:
        """Save content as PDF file.

        Args:
            content: Text content to save

        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            save_path = await self.window.save_file_dialog(
                "Save PDF File",
                suggested_filename="research_report.pdf",
                file_types=["pdf"],
            )
            if save_path and str(save_path).strip():
                # TODO: Implement PDF conversion
                logger.warning("PDF export not yet implemented")
                return None
            return None
        except Exception:
            logger.exception("Error saving PDF file")
        return None

    async def save_docx(self, content: str) -> Path | None:
        """Save content as DOCX file.

        Args:
            content: Text content to save

        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            save_path = await self.window.save_file_dialog(
                "Save Word Document",
                suggested_filename="research_report.docx",
                file_types=["docx"],
            )
            if save_path and str(save_path).strip():
                # TODO: Implement DOCX conversion
                logger.warning("DOCX export not yet implemented")
                return None
            return None
        except Exception:
            logger.exception("Error saving DOCX file")
            return None

    async def save_json_log(
        self,
        query: str,
        report_type: str,
        tone: str,
        source: str,
        costs: float,
        sources: list[str],
    ) -> Path | None:
        """Save research log as JSON file.

        Args:
            query: Research query
            report_type: Type of report
            tone: Report tone
            source: Research source
            costs: Total costs
            sources: List of source URLs

        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            save_path = await self.window.save_file_dialog(
                "Save Log File",
                suggested_filename="research_log.json",
                file_types=["json"],
            )
            if save_path and str(save_path).strip():
                # Create log data
                log_data: dict[str, Any] = {
                    "query": query,
                    "report_type": report_type,
                    "tone": tone,
                    "source": source,
                    "timestamp": str(datetime.now()),
                    "costs": costs,
                    "sources": sources,
                }
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=2)
                return Path(save_path)
            return None
        except Exception:
            logger.exception("Error saving JSON log")
            return None
