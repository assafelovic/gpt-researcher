"""Onboarding component for the GPT Researcher application."""

from __future__ import annotations

from typing import Any, Callable, Optional

from standalone_app.features.settings.constants import COLORS
from toga import Box, Button, Label, Widget, Window
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]


class OnboardingOverlay:
    """An onboarding overlay that guides users through the application's features."""

    def __init__(
        self,
        parent_window: Window,
        on_complete: Optional[Callable[[], None]] = None,
    ):
        """Initialize the onboarding overlay."""
        self._parent_window: Window = parent_window
        self._on_complete: Optional[Callable[[], None]] = on_complete
        self._current_step: int = 0
        self._steps: list[dict[str, Any]] = [
            {
                "title": "Welcome to Autonomous Researcher!",
                "description": "This guided tour will help you understand how to use the application.",
                "target": None,
            },
            {
                "title": "Research Query",
                "description": "Enter your research topic in this text area. Be specific and clear about what you want to research. Keeping your prompt short, but detailed, will help the AI generate a more accurate and relevant report.",
                "target": "input_section.query_input",
            },
            {
                "title": "Start Research",
                "description": "Click the 'Research' button to begin your autonomous research process.",
                "target": "input_section.submit_button",
            },
            {
                "title": "Previous Conversations",
                "description": "Access and restore your previous research sessions from the side panel.",
                "target": "previous_research_panel.panel_container",
            },
        ]
        self._create_overlay()

    def _create_overlay(self):
        """Create the overlay components."""
        # Create a dark overlay that covers the entire window
        self.overlay_box: Box = Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
                background_color="#000000",
                padding=20,
            )
        )

        # Create boxes for the spotlight effect
        self.top_overlay: Box = Box(
            style=Pack(
                flex=1,
                background_color="#000000",
            )
        )
        self.overlay_box.add(self.top_overlay)

        # Middle row with spotlight
        self.middle_row: Box = Box(
            style=Pack(
                direction=ROW,
                flex=0,
            )
        )
        self.left_overlay: Box = Box(
            style=Pack(
                flex=1,
                background_color="#000000",
            )
        )
        self.spotlight_box: Box = Box(
            style=Pack(
                flex=0,
                background_color="transparent",
            )
        )
        self.right_overlay: Box = Box(
            style=Pack(
                flex=1,
                background_color="#000000",
            )
        )
        self.middle_row.add(self.left_overlay)
        self.middle_row.add(self.spotlight_box)
        self.middle_row.add(self.right_overlay)
        self.overlay_box.add(self.middle_row)

        self.bottom_overlay: Box = Box(
            style=Pack(
                flex=1,
                background_color="#000000",
            )
        )
        self.overlay_box.add(self.bottom_overlay)

        # Content box for the tooltip
        self.content_box: Box = Box(
            style=Pack(
                direction=COLUMN,
                padding=20,
                background_color=COLORS.get("card", "#FFFFFF"),
                width=400,
            )
        )

        # Title
        self.title_label: Label = Label(
            "",
            style=Pack(
                font_size=24,
                font_weight="bold",
                padding=(0, 0, 10, 0),
                color=COLORS["text"],
                alignment=CENTER,
            ),
        )
        self.content_box.add(self.title_label)

        # Description
        self.description_label: Label = Label(
            "",
            style=Pack(
                padding=(0, 0, 20, 0),
                color=COLORS["text_secondary"],
                font_size=14,
                alignment=CENTER,
            ),
        )
        self.content_box.add(self.description_label)

        # Navigation buttons
        button_box: Box = Box(style=Pack(direction=ROW, alignment=CENTER))

        # Skip button
        self.skip_button: Button = Button(
            "Skip",
            on_press=self.finish,
            style=Pack(
                padding=5,
                background_color=COLORS["background"],
                color=COLORS["text"],
                width=80,
                height=35,
            ),
        )
        button_box.add(self.skip_button)

        # Previous button
        self.prev_button: Button = Button(
            "Previous",
            on_press=self.previous_step,
            style=Pack(
                padding=5,
                background_color=COLORS["background"],
                color=COLORS["text"],
                width=100,
                height=35,
            ),
        )
        self.prev_button.enabled = False
        button_box.add(self.prev_button)

        # Next button
        self.next_button: Button = Button(
            "Next",
            on_press=self.next_step,
            style=Pack(
                padding=5,
                background_color=COLORS["primary"],
                color=COLORS["card"],
                width=80,
                height=35,
                font_weight="bold",
            ),
        )
        button_box.add(self.next_button)

        self.content_box.add(button_box)
        self.overlay_box.add(self.content_box)

    def _update_content(self):
        """Update the content for the current step."""
        step: dict[str, Any] = self._steps[self._current_step]
        self.title_label.text = step["title"]
        self.description_label.text = step["description"]

        # Update button states
        self.prev_button.enabled = self._current_step > 0
        is_last_step = self._current_step == len(self._steps) - 1
        self.next_button.text = "Finish" if is_last_step else "Next"

        # Highlight target element if specified
        if step["target"]:
            self._highlight_element(step["target"])

    def _highlight_element(self, target: str):
        """Create a spotlight effect around the target element."""
        # Get the target element
        target_parts: list[str] = target.split(".")
        current_obj: Any = self._parent_window
        for part in target_parts:
            current_obj = getattr(current_obj, part, None)
            if current_obj is None:
                break

        if current_obj:
            # Show middle row with spotlight
            self.middle_row.style.visibility = "visible"
            self.top_overlay.style.visibility = "visible"
            self.bottom_overlay.style.visibility = "visible"

            # Get target element's size if available
            target_style = current_obj.style
            if target_style:
                height = target_style.height
                width = target_style.width

                # Update spotlight box size
                self.spotlight_box.style.update(
                    width=width,
                    height=height,
                    flex=0,  # Don't grow
                )

                # Update overlays to create the spotlight effect
                self.top_overlay.style.update(flex=1)
                self.bottom_overlay.style.update(flex=1)
                self.left_overlay.style.update(flex=1)
                self.right_overlay.style.update(flex=1)
        else:
            # Hide all overlay elements if target not found
            self.middle_row.style.visibility = "hidden"
            self.top_overlay.style.visibility = "hidden"
            self.bottom_overlay.style.visibility = "hidden"

    def next_step(self, widget: Widget):
        """Move to the next step or finish onboarding."""
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._update_content()
        else:
            self.finish()

    def previous_step(self, widget: Widget):
        """Move to the previous step."""
        if self._current_step > 0:
            self._current_step -= 1
            self._update_content()

    def start(self):
        """Start the onboarding process."""
        # Store the current window content before starting
        self._original_content: Widget | None = self._parent_window.content
        self._current_step: int = 0
        self._update_content()
        self._parent_window.content = self.overlay_box

    def finish(self, widget: Widget | None = None):
        """Complete the onboarding process."""
        if self._on_complete is not None:
            self._on_complete()
        # Restore the original window content
        if self._original_content is not None:
            self._parent_window.content = self._original_content
            self._original_content = None
