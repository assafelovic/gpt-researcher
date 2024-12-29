"""Utility functions for settings and UI management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from toga import Label
from toga.style import Pack

if TYPE_CHECKING:
    from toga import Box, Switch


def toggle_visibility(
    container: Box,
    widget: Switch,
    collapse_height: int = 0,
    collapse_padding: int = 0,
) -> None:
    """
    Toggle the visibility of a container based on a switch's value.

    Args:
        container (Box): The container to toggle visibility for
        widget (Switch): The switch controlling visibility
        collapse_height (int, optional): Height when collapsed. Defaults to 0.
        collapse_padding (int, optional): Padding when collapsed. Defaults to 0.
    """
    if widget.value:
        container.style.visibility = "visible"
        # Remove height and padding constraints
        if hasattr(container.style, "height"):
            del container.style.height
        if hasattr(container.style, "padding"):
            del container.style.padding
    else:
        container.style.visibility = "hidden"
        container.style.height = collapse_height
        container.style.padding = collapse_padding


def create_section_label(
    text: str,
    style: dict | None = None,
) -> Label:
    """
    Create a consistent section label with optional custom styling.

    Args:
        text (str): Label text
        style (dict, optional): Custom style dictionary

    Returns:
        Label: A styled label for section headers
    """

    default_style = {"font_weight": "bold", "font_size": 16, "padding": (10, 0)}

    # Merge default style with any custom style
    merged_style = {**default_style, **(style or {})}

    return Label(text, style=Pack(**merged_style))
