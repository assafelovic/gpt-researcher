"""Split layout component for the GPT Researcher application."""

from __future__ import annotations

from typing import Optional

from toga import Box, ScrollContainer, SplitContainer, Widget
from toga.style import Pack

from standalone_app.features.ui.sections.previous_research import PreviousResearchPanel


class SplitLayout:
    """Split layout with main content and side panel."""

    def __init__(self):
        """Initialize the split layout."""
        self._create_layout()

    def _create_layout(self):
        """Create the split layout with side panel."""
        # Create split container
        self.split_container: SplitContainer = SplitContainer(
            style=Pack(flex=1)
        )

        # Create side panel for previous research
        self.previous_research: PreviousResearchPanel = PreviousResearchPanel()
        self.split_container.add(self.previous_research.panel_container)

        # Create main content area
        self.main_scroll: ScrollContainer = ScrollContainer(
            style=Pack(flex=1)
        )
        self.split_container.add(self.main_scroll)

    @property
    def content(self) -> Widget | None:
        """Get the main content box."""
        return self.main_scroll.content

    @content.setter
    def content(self, value: Box):
        """Set the main content box."""
        self.main_scroll.content = value

    def get_container(self) -> SplitContainer:
        """Get the split container."""
        return self.split_container

    def add_research_item(
        self,
        query: str,
        report_type: str,
        widget: Widget | None = None,
    ):
        """Add a research item to the previous research panel."""
        self.previous_research.add_research_item(query, report_type, widget)
