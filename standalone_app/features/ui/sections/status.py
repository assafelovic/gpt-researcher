"""Status section component for the GPT Researcher application."""

from __future__ import annotations

from standalone_app.features.settings.constants import APP_STYLES, COLORS
from toga import Box, Label
from toga.style import Pack
from toga.style.pack import COLUMN  # pyright: ignore[reportPrivateImportUsage]


class StatusSection:
    """Status section for displaying research progress and messages."""

    def __init__(self):
        """Initialize the status section."""
        self._create_status_section()

    def _create_status_section(self):
        """Create the status section."""
        self.status_box: Box = Box(style=Pack(direction=COLUMN, padding=(5, 0)))
        self.status_label: Label = Label("Ready to research", style=APP_STYLES["status_label"])
        self.progress_label: Label = Label(
            "",  # Initially empty
            style=Pack(
                padding=(5, 0),
                font_size=14,
                color=COLORS["text_secondary"],
                visibility="hidden",
            ),
        )

        self.status_box.add(self.status_label)
        self.status_box.add(self.progress_label)

    def set_status(
        self,
        message: str,
        color_type: str = "text",
    ):
        """
        Set the status message and its color.

        :param message: Status message to display
        :param color_type: Color type from COLORS (e.g., 'text', 'success', 'warning', 'danger')
        """
        assert self.status_label is not None
        self.status_label.text = message
        self.status_label.style.color = COLORS.get(color_type, COLORS["text"])

    def set_progress(
        self,
        message: str,
        visible: bool = True,
    ):
        """
        Set the progress message.

        :param message: Progress message to display
        :param visible: Whether to make the progress label visible
        """
        assert self.progress_label is not None
        self.progress_label.text = message
        self.progress_label.style.visibility = "visible" if visible else "hidden"
