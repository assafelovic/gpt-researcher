"""Input section component for the GPT Researcher application."""

from __future__ import annotations

from typing import Any, Callable

from standalone_app.features.settings.constants import COLORS
from toga import Box, Button, MultilineTextInput
from toga.style import Pack


class InputSection:
    """Input section for research query and settings."""

    def __init__(
        self,
        on_research: Callable[[], Any],
        on_settings: Callable[[], Any],
    ):
        """Initialize the input section."""

        self._on_research: Callable[[], Any] = on_research
        self._on_settings: Callable[[], Any] = on_settings

        self._create_input_section()

    def _create_input_section(self):
        """Create the query input section."""
        # Create a container with flexible layout
        self.input_container: Box = Box(
            style=Pack(
                direction="column",
                padding=10,
                flex=1,  # Take full available space
            )
        )

        # Create a scrollable multiline text input that expands
        self.query_input: MultilineTextInput = MultilineTextInput(
            placeholder="Enter your research query here...",
            style=Pack(
                flex=1,  # Expand to fill available space
                padding=10,
                background_color=COLORS.get("input_background", "white"),
            )
        )

        # Create a horizontal box for buttons
        button_box = Box(
            style=Pack(
                direction="row",
                padding=(10, 0, 0, 0),
            )
        )

        # Research button - always at the bottom
        self.submit_button: Button = Button(
            "Research",
            on_press=self._on_research,
            style=Pack(
                flex=1,
                padding=10,
                background_color=COLORS.get("primary_button", "blue"),
                color="white",
            )
        )

        # Settings button with centered icon
        self.settings_button: Button = Button(
            "⚙",  # Gear icon
            on_press=self._on_settings,
            style=Pack(
                width=50,
                height=50,
                padding=10,
                text_align="center",
                background_color=COLORS.get("secondary_button", "lightgray"),
            )
        )

        # Add buttons to button box
        button_box.add(self.submit_button)
        button_box.add(self.settings_button)

        # Add components to input container
        self.input_container.add(self.query_input)
        self.input_container.add(button_box)

    def get_query(self) -> str:
        """Get the current query input value."""
        return self.query_input.value or ""

    def disable_input(self):
        """Disable input fields during research."""
        self.query_input.enabled = False
        self.submit_button.enabled = False
        self.settings_button.enabled = False

    def enable_input(self):
        """Re-enable input fields after research."""
        self.query_input.enabled = True
        self.submit_button.enabled = True
        self.settings_button.enabled = True
