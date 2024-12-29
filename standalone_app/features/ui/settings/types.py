"""Input type components for settings dialog."""

from __future__ import annotations

from standalone_app.features.settings.constants import APP_STYLES, STYLES
from standalone_app.features.ui.components.selection import Selection
from toga import Box, Label, TextInput


class SelectionInput:
    """Selection input component with label."""

    def __init__(self, label: str, items: list[str], default: str):
        """Initialize selection input."""
        self.container: Box = Box(style=APP_STYLES["input_container"])

        self.label: Label = Label(
            label,
            style=STYLES["label"],
        )

        self.selection: Selection = Selection(
            items=items,
            value=default,
            style=STYLES["selection"],
        )

        self.container.add(self.label)
        self.container.add(self.selection)


class TextInputSettings:
    """Text input component with label and hint."""

    def __init__(self, label: str, default: str, hint: str | None = None):
        """Initialize text input."""
        self.container: Box = Box(style=APP_STYLES["input_container"])

        self.label: Label = Label(
            label,
            style=STYLES["label"],
        )

        self.input: TextInput = TextInput(
            value=default,
            placeholder=hint or "",
            style=STYLES["input"],
        )

        self.container.add(self.label)
        self.container.add(self.input)
