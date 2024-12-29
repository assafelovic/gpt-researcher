"""Previous Research Dock Panel for the GPT Researcher application."""

from __future__ import annotations

from typing import List, Optional, Callable
from datetime import datetime

from toga import Box, Label, Button, ScrollContainer
from toga.style import Pack
from toga.style.pack import COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]

from standalone_app.features.settings.constants import COLORS, STYLES


class PreviousResearchPanel:
    """A side panel to manage and restore previous research sessions."""

    def __init__(
        self, 
        on_restore_research: Optional[Callable[[str], None]] = None
    ):
        """Initialize the previous research panel."""
        self._on_restore_research = on_restore_research
        self._research_history: List[dict] = []
        self._create_panel()

    def _create_panel(self):
        """Create the dock panel for previous research."""
        # Main container for the dock panel
        self.panel_container: Box = Box(
            style=Pack(
                direction=COLUMN,
                padding=10,
                width=300,  # Fixed width for the dock panel
                background_color=COLORS.get("background", "white")
            )
        )

        # Header for the panel
        header = Label(
            "Recent",
            style=Pack(
                font_size=16,
                font_weight="bold",
                padding=(0, 0, 10, 0),
                color=COLORS.get("text", "black")
            )
        )
        self.panel_container.add(header)

        # Scrollable container for research history
        self.research_list_container: ScrollContainer = ScrollContainer(
            style=Pack(
                flex=1,
                padding=(0, 5)
            )
        )

        # Box to hold research items
        self.research_list_box: Box = Box(
            style=Pack(
                direction=COLUMN,
            )
        )
        self.research_list_container.content = self.research_list_box

        self.panel_container.add(self.research_list_container)

    def add_research_item(self, query: str, report_type: str, timestamp: Optional[datetime] = None):
        """Add a new research item to the history."""
        if timestamp is None:
            timestamp = datetime.now()

        # Create a research item box
        research_item = Box(
            style=Pack(
                direction=ROW,
                padding=5,
            )
        )

        # Research details
        details_box = Box(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )
        query_label = Label(
            query,
            style=Pack(
                font_weight="bold",
                font_size=14,
                text_overflow="ellipsis"
            )
        )
        type_label = Label(
            f"{report_type} - {timestamp.strftime('%Y-%m-%d %H:%M')}",
            style=Pack(
                font_size=12,
                color=COLORS.get("text_secondary", "gray")
            )
        )
        details_box.add(query_label)
        details_box.add(type_label)

        # Restore button
        restore_button = Button(
            "Restore",
            on_press=lambda w, q=query: self._restore_research(q),
            style=Pack(
                padding=5,
                background_color=COLORS.get("primary_button", "blue"),
                color="white"
            )
        )

        research_item.add(details_box)
        research_item.add(restore_button)

        self.research_list_box.add(research_item)
        self._research_history.append({
            "query": query,
            "report_type": report_type,
            "timestamp": timestamp
        })

    def _restore_research(self, query: str):
        """Restore a previous research session."""
        if self._on_restore_research:
            self._on_restore_research(query)

    def clear_history(self):
        """Clear all research history."""
        self.research_list_box.clear()
        self._research_history.clear()

    def get_research_history(self) -> List[dict]:
        """Get the current research history."""
        return self._research_history.copy()