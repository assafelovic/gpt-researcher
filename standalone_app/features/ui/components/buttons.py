"""Action buttons component for the GPT Researcher application."""

from __future__ import annotations

from typing import Any, Callable

from toga import Box, Button
from toga.style import Pack
from toga.style.pack import ROW  # pyright: ignore[reportPrivateImportUsage]


class ActionButtons:
    """Action buttons for copying and downloading research results."""

    def __init__(
        self,
        on_copy: Callable[[], Any],
        on_download_md: Callable[[], Any],
        on_download_pdf: Callable[[], Any],
        on_download_docx: Callable[[], Any],
        on_download_json: Callable[[], Any],
    ):
        """
        Initialize action buttons.

        :param on_copy: Callback for copying results to clipboard
        :param on_download_md: Callback for downloading as Markdown
        :param on_download_pdf: Callback for downloading as PDF
        :param on_download_docx: Callback for downloading as DOCX
        :param on_download_json: Callback for downloading log
        """

        self._on_copy: Callable[[], Any] = on_copy
        self._on_download_md: Callable[[], Any] = on_download_md
        self._on_download_pdf: Callable[[], Any] = on_download_pdf
        self._on_download_docx: Callable[[], Any] = on_download_docx
        self._on_download_json: Callable[[], Any] = on_download_json

        self._create_action_buttons()

    def _create_action_buttons(self):
        """Create the action buttons section."""
        self.action_box: Box = Box(style=Pack(direction=ROW, padding=(10, 5)))

        self.copy_button: Button = Button(
            "Copy to Clipboard",
            on_press=self._on_copy,
            style=Pack(padding=(0, 5), height=35),
            enabled=False,
        )
        self.download_md_button: Button = Button(
            "Download as MD",
            on_press=self._on_download_md,
            style=Pack(padding=(0, 5), height=35),
            enabled=False,
        )
        self.download_pdf_button: Button = Button(
            "Download as PDF",
            on_press=self._on_download_pdf,
            style=Pack(padding=(0, 5), height=35),
            enabled=False,
        )
        self.download_docx_button: Button = Button(
            "Download as DOCX",
            on_press=self._on_download_docx,
            style=Pack(padding=(0, 5), height=35),
            enabled=False,
        )
        self.download_json_button: Button = Button(
            "Download Log",
            on_press=self._on_download_json,
            style=Pack(padding=(0, 5), height=35),
            enabled=False,
        )

        self.action_box.add(self.copy_button)
        self.action_box.add(self.download_md_button)
        self.action_box.add(self.download_pdf_button)
        self.action_box.add(self.download_docx_button)
        self.action_box.add(self.download_json_button)

    def update_button_states(self, enabled: bool = True):
        """
        Update the state of action buttons.

        :param enabled: Whether buttons should be enabled
        """
        assert self.copy_button is not None
        self.copy_button.enabled = enabled

        assert self.download_md_button is not None
        self.download_md_button.enabled = enabled

        assert self.download_pdf_button is not None
        self.download_pdf_button.enabled = enabled

        assert self.download_docx_button is not None
        self.download_docx_button.enabled = enabled

        assert self.download_json_button is not None
        self.download_json_button.enabled = enabled
