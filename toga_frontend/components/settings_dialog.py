from __future__ import annotations

import os

from typing import TYPE_CHECKING, Callable

from toga import Box, Button, Label, TextInput, Window
from toga.style import Pack
from toga.style.pack import COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from toga import Widget

    from toga_frontend.app import GPTResearcherApp


class SettingsWindow(Window):
    def __init__(
        self,
        app: GPTResearcherApp,
        on_save: Callable | None = None,
    ):
        super().__init__(
            title="Settings",
            size=(400, 200),
            id="settings_window",
        )

        self._parent_app: GPTResearcherApp = app
        self.on_save: Callable | None = on_save

        # Create and set content
        self.content = self._create_content()

    def _create_content(self) -> Box:
        box = Box(style=Pack(direction=COLUMN, padding=10))

        # OpenAI API Key
        openai_box = Box(style=Pack(direction=ROW, padding=(0, 0, 5, 0)))
        openai_label = Label("OpenAI API Key:", style=Pack(padding_right=10))
        self.openai_input: TextInput = TextInput(value=os.getenv("OPENAI_API_KEY", ""), style=Pack(flex=1))
        openai_box.add(openai_label)
        openai_box.add(self.openai_input)

        # Tavily API Key
        tavily_box = Box(style=Pack(direction=ROW, padding=(0, 0, 5, 0)))
        tavily_label = Label("Tavily API Key:", style=Pack(padding_right=10))
        self.tavily_input: TextInput = TextInput(value=os.getenv("TAVILY_API_KEY", ""), style=Pack(flex=1))
        tavily_box.add(tavily_label)
        tavily_box.add(self.tavily_input)

        # Buttons
        button_box = Box(style=Pack(direction=ROW, padding=(10, 0, 0, 0)))
        save_button: Button = Button("Save", on_press=self._save_settings, style=Pack(flex=1, padding=5))
        cancel_button = Button("Cancel", on_press=self._cancel, style=Pack(flex=1, padding=5))
        button_box.add(save_button)
        button_box.add(cancel_button)

        # Add all sections
        box.add(openai_box)
        box.add(tavily_box)
        box.add(button_box)

        return box

    def _save_settings(
        self,
        widget: Widget,
    ):
        """Save the API keys to environment variables."""
        os.environ["OPENAI_API_KEY"] = self.openai_input.value
        os.environ["TAVILY_API_KEY"] = self.tavily_input.value

        if self.on_save:
            self.on_save()

        self.close()

    def _cancel(
        self,
        widget: Widget,
    ):
        """Close the window without saving."""
        self.close()

    def show(self):
        """Show the settings window."""
        # The app property is automatically set by Toga when the window is created
        self.app.windows.add(self)
        super().show()

    def close(self):
        """Close the settings window."""
        self.app.windows.remove(self)
        super().close()
