"""Results section component for the GPT Researcher application."""

from __future__ import annotations

from standalone_app.features.settings.constants import APP_STYLES
from toga import Box, MultilineTextInput, ScrollContainer
from toga.style import Pack
from toga.style.pack import COLUMN  # pyright: ignore[reportPrivateImportUsage]


class ResultsSection:
    """Results section for displaying research output."""

    def __init__(self):
        """Initialize the results section."""
        self._create_results_section()

    def _create_results_section(self):
        """Create the results section."""
        self.results_container: ScrollContainer = ScrollContainer(style=APP_STYLES["results_container"])
        self.results_box: Box = Box(style=Pack(direction=COLUMN))
        self.results_content: MultilineTextInput = MultilineTextInput(
            readonly=True,
            style=APP_STYLES["results_content"],
            placeholder="Research results will appear here",
        )

        self.results_box.add(self.results_content)
        self.results_container.content = self.results_box

    def set_results(self, results: str):
        """
        Set the results content.

        :param results: Research results to display
        """
        assert self.results_content is not None
        self.results_content.value = results

    def clear_results(self):
        """Clear the results content."""
        assert self.results_content is not None
        self.results_content.value = ""

    def get_results(self) -> str:
        """
        Get the current results content.

        :return: Current results as a string
        """
        assert self.results_content is not None
        return self.results_content.value or ""
