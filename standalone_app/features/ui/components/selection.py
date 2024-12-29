"""Custom Selection widget with disabled mouse wheel scrolling on Windows."""

from __future__ import annotations

import contextlib

from typing import Any, Callable

from toga import Box, Button, Selection as BaseSelection
from toga.style import Pack


class Selection(BaseSelection):
    """Selection widget with disabled mouse wheel scrolling on Windows."""

    def __init__(
        self,
        id: str | None = None,
        style: Pack | None = None,
        items: list[Any] | None = None,
        accessor: str | None = None,
        value: Any | None = None,
        on_change: Callable[[Selection], None] | None = None,
        enabled: bool = True,
    ):
        """Initialize the selection widget.

        Args:
            id: The ID for the widget
            style: A style object
            items: Initial items to display
            accessor: The accessor to use to extract display values
            value: Initial value for the selection
            on_change: Initial on_change handler
            enabled: Whether the user can interact with the widget
        """
        # Create container for selection and reset button
        self.container: Box = Box(
            style=Pack(
                direction="row",
                padding=0,
                flex=1,
            )
        )

        # Store default value
        self._default_value: Any = value

        # Create reset button
        self.reset_button: Button = Button(
            "Reset",
            style=Pack(
                padding_left=5,
                visibility="hidden",
            ),
            on_press=lambda _: self._do_reset(),
        )

        # Initialize base selection
        super().__init__(
            id=id,
            style=style,
            items=items,
            accessor=accessor,
            value=value,
            enabled=enabled,
            on_change=on_change,
        )

        # Wrap original on_change handler
        self._original_on_change: Callable[[Selection], None] | None = on_change

        # Add widgets to container
        self.container.add(self)
        self.container.add(self.reset_button)

        # Disable mouse wheel on Windows
        if hasattr(self._impl, "native"):
            with contextlib.suppress(Exception):
                def handle_mouse_wheel(sender: Any, event: Any) -> None:
                    event.Handled = True
                self._impl.native.MouseWheel += handle_mouse_wheel

    def _handle_change(
        self,
        widget: Selection,
    ) -> None:
        """Handle changes to selection value."""
        # Show/hide reset button based on modification
        self.reset_button.style.visibility = "visible" if self.value != self._default_value else "hidden"

        # Call original handler if it exists
        if self._original_on_change:
            self._original_on_change(widget)

    def _do_reset(self) -> None:
        """Reset selection to default value."""
        self.value = self._default_value
        self.reset_button.style.visibility = "hidden"
