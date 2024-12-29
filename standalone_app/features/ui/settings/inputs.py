"""Custom input components for settings dialog."""

from __future__ import annotations

import asyncio
import os
import webbrowser

from typing import TYPE_CHECKING

from standalone_app.features.settings.constants import (
    API_PROVIDER_URLS,
    COLORS,
    STYLES,  # pyright: ignore[reportPrivateImportUsage]
    ValidationStatus,
)
from standalone_app.features.ui.components.selection import Selection
from toga import Box, Button, Label, PasswordInput, Switch, TextInput
from toga.style import Pack
from toga.style.pack import COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from typing_extensions import Callable, ClassVar


class APIKeyInput(Box):
    """
    Custom input for API keys with validation and reset functionality.
    Provides:
    - Input field for API key (password protected)
    - Validation status
    - Reset functionality
    - Option to open provider's key generation page.
    """

    def __init__(
        self,
        key_name: str,
        display_name: str,
        tooltip: str,
        provider_key: str,
    ):
        """
        Initialize the API key input.

        :param key_name: Environment variable name for the API key
        :param display_name: Human-readable name of the API key
        :param tooltip: Description of the API key's purpose
        :param provider_key: Key to look up in API_PROVIDER_URLS
        """
        super().__init__(style=Pack(direction=COLUMN, padding=(0, 0, 2, 0)))

        self.key_name: str = key_name
        self.tooltip: str = tooltip
        self.default_value: str = os.getenv(key_name, "")
        self.is_modified: bool = False

        # Create UI components that need to be accessed later
        self.input: PasswordInput
        self.validation_label: Label
        self.reset_button: Button
        self.error_label: Label

        self._create_ui(display_name, provider_key)

    def _create_ui(self, display_name: str, provider_key: str):
        """Create the UI components."""
        # Create input box with label and validation status
        input_box = Box(style=Pack(direction=ROW, padding=(5, 0)))

        # Create label
        label = Label(
            display_name + ":",
            style=Pack(
                padding=(0, 5),
                width=150,
                font_size=14,
                color=COLORS["text"],
            ),
        )
        input_box.add(label)

        # Create input
        self.input = PasswordInput(
            value=self.default_value,
            placeholder=f"Enter your {display_name}",
            style=Pack(
                flex=1,
                padding=5,
                height=35,
            ),
            on_change=self._handle_input_change,
        )
        input_box.add(self.input)

        # Create validation status label
        self.validation_label = Label(
            ValidationStatus.NONE,
            style=Pack(
                padding=(0, 5),
                width=20,
                font_size=14,
                color=COLORS["text"],
            ),
        )
        input_box.add(self.validation_label)

        # Create reset button
        self.reset_button: Button = Button(
            "Reset",
            on_press=self._handle_reset,
            style=Pack(
                padding=5,
                background_color=COLORS["warning"],
                color=COLORS["card"],
                font_weight="bold",
                visibility="hidden",
            ),
        )
        input_box.add(self.reset_button)

        # Create "Get Key" button
        if provider_key in API_PROVIDER_URLS:
            get_key_button = Button(
                "Get Key",
                on_press=lambda widget: webbrowser.open(API_PROVIDER_URLS[provider_key]),
                style=Pack(
                    padding=5,
                    background_color=COLORS["primary"],
                    color=COLORS["card"],
                    font_weight="bold",
                ),
            )
            input_box.add(get_key_button)

        self.add(input_box)

        # Create error label
        self.error_label = Label(
            "",
            style=Pack(
                padding=(0, 5),
                font_size=12,
                font_style="italic",
                color=COLORS["danger"],
                visibility="hidden",
            ),
        )
        self.add(self.error_label)

        # Create tooltip label
        tooltip_label = Label(
            self.tooltip,
            style=Pack(
                padding=(0, 5),
                font_size=12,
                font_style="italic",
                color=COLORS["text_secondary"],
            ),
        )
        self.add(tooltip_label)

    def _handle_input_change(self, widget: PasswordInput):
        """
        Handle changes to the input field.

        :param widget: The text input widget
        """
        self.is_modified = widget.value != self.default_value
        self.reset_button.style.visibility = "visible" if self.is_modified else "hidden"
        self.validation_label.text = ValidationStatus.NONE

    def _handle_reset(
        self,
        widget: Button,
    ):
        """
        Reset the input to its default value.

        :param widget: The reset button widget
        """
        self.input.value = self.default_value
        self.is_modified = False
        self.reset_button.style.visibility = "hidden"
        self.validation_label.text = ValidationStatus.NONE
        self.error_label.style.visibility = "hidden"

    async def validate_api_key(self) -> bool:
        """
        Validate the API key by checking its basic properties.

        :return: True if the key passes basic validation, False otherwise
        """
        self.validation_label.text = ValidationStatus.LOADING
        self.error_label.style.visibility = "hidden"

        try:
            if not self.input.value:
                raise ValueError("API key is required")

            if len(self.input.value) < 8:
                raise ValueError("API key is too short")

            # TODO: async validation to the actual API provider.
            # This is a placeholder for now.
            await asyncio.sleep(0.5)

            self.validation_label.text = ValidationStatus.VALID
            return True

        except Exception as e:
            self.validation_label.text = ValidationStatus.INVALID
            self.error_label.text = str(e)
            self.error_label.style.visibility = "visible"
            return False


class SettingsInput:
    """Base class for settings inputs with modification tracking."""

    def __init__(
        self,
        label_text: str,
        default_value: str,
        on_reset: Callable[[], None] | None = None,
    ):
        """
        Initialize a settings input.

        :param label_text: Text for the input label
        :param default_value: Default input value
        """
        self._on_reset: Callable[[], None] | None = on_reset
        self.default_value: str = default_value
        self.is_modified: bool = False

        # Create container
        self.container: Box = Box(style=Pack(direction="row", padding=5))

        # Add label
        self.container.add(Label(label_text, style=STYLES["label"]))

        # Create input container
        self.input_container: Box = Box(style=Pack(direction="row", flex=1))
        self.container.add(self.input_container)

        # Add reset button
        self.reset_button: Button = Button(
            "Reset",
            style=Pack(
                padding_left=5,
                visibility="hidden",
            ),
            on_press=lambda _: self._do_reset(),
        )
        self.input_container.add(self.reset_button)

    def _do_reset(self):
        """Reset input to default value. Must be implemented by subclasses."""
        raise NotImplementedError()

    @property
    def value(self) -> str:
        """Get the current input value. Must be implemented by subclasses."""
        raise NotImplementedError()


class ModelSelectionInput(SettingsInput):
    """Selection input for AI models with category support."""

    # Class variables
    CATEGORIES: ClassVar[dict[str, str]] = {
        "Trial Models (Free Account Required)": "trial",
        "Free Models (No Account Required)": "free",
        "Paid Models (API Key Required)": "paid",
    }

    def __init__(
        self,
        label_text: str,
        categories: dict[str, list[str]],
        default_value: str,
    ):
        """
        Initialize a model selection input with categories.

        Args:
            label_text: Text for the input label
            categories: Dictionary of category names to lists of model names
            default_value: Default selected value
        """
        super().__init__(label_text, default_value)

        # Initialize current selection
        self._current_selection: str | None = default_value

        # Store model lists by category type
        self.model_lists: dict[str, list[str]] = {}

        # Find default category
        default_category: str | None = None
        for category_name, models in categories.items():
            if not models:  # Skip empty categories
                continue
            # Determine category type (trial/free/paid)
            category_type: str = "trial"  # Default to trial
            if "No Account Required" in category_name or "No API Key Required" in category_name:
                category_type = "free"
            elif "API Key Required" in category_name or "Paid" in category_name:
                category_type = "paid"

            # Add models to appropriate category
            if category_type not in self.model_lists:
                self.model_lists[category_type] = []
            self.model_lists[category_type].extend(models)

            # Check if this category contains the default value
            if default_value in models:
                default_category = next(cat for cat, type_ in self.CATEGORIES.items() if type_ == category_type)

        # Create main container
        self.selection_container: Box = Box(style=Pack(direction="column", padding=(0, 0, 10, 0), flex=1))

        # Create category selection
        category_label = Label(
            "Model Category:",
            style=Pack(
                padding=(5, 0),
                font_size=14,
                font_weight="bold",
                color=COLORS["text"],
            ),
        )

        # Create box for category selection
        category_box = Box(style=Pack(direction="row", padding=(0, 5), flex=1))
        self.category_selection = Selection(
            items=list(self.CATEGORIES.keys()),
            value=default_category or list(self.CATEGORIES.keys())[0],  # Default to first category if not found
            style=Pack(flex=1),
            on_change=self._handle_category_change,
        )

        category_box.add(self.category_selection.container)

        # Create model selection
        model_label = Label(
            "Select Model:",
            style=Pack(
                padding=(10, 0),
                font_size=14,
                font_weight="bold",
                color=COLORS["text"],
            ),
        )

        # Create box for model selection
        model_box = Box(style=Pack(direction="row", padding=(0, 5), flex=1))  # Added flex=1 to expand the box
        self.model_selection: Selection = Selection(
            items=[],  # Will be populated in _handle_category_change
            style=Pack(flex=1),
            on_change=self._handle_model_change,
        )

        model_box.add(self.model_selection.container)

        # Add everything to the container
        self.selection_container.add(category_label)
        self.selection_container.add(category_box)
        self.selection_container.add(model_label)
        self.selection_container.add(model_box)

        # Insert selection container before reset button
        self.input_container.insert(0, self.selection_container)

        # Initialize model selection with appropriate models
        self._handle_category_change(self.category_selection)

    def _handle_category_change(self, widget: Selection):
        """Handle changes to category selection."""
        category_type = self.CATEGORIES[str(widget.value)]
        models = self.model_lists.get(category_type, [])

        # Update model selection
        self.model_selection.items = models

        # Try to keep current selection if it's in the new category
        if self._current_selection in models:
            self.model_selection.value = self._current_selection
        else:
            self.model_selection.value = models[0] if models else None
            if models:  # Only update if we have models
                self._current_selection = str(models[0])

    def _handle_model_change(self, widget: Selection):
        """Handle changes to model selection."""
        if widget.value is None:
            return

        new_value = str(widget.value)
        if new_value != self._current_selection:
            self._current_selection = new_value
            self.is_modified = new_value != self.default_value
            self.reset_button.style.visibility = "visible" if self.is_modified else "hidden"

    def _do_reset(self):
        """Reset selection to default value."""
        # Find category containing default value
        for category_name, category_type in self.CATEGORIES.items():
            if self.default_value in self.model_lists.get(category_type, []):
                self.category_selection.value = category_name
                self._handle_category_change(self.category_selection)
                self.model_selection.value = self.default_value
                self._current_selection = self.default_value
                break

    @property
    def value(self) -> str:
        """Get the current selection value."""
        return self._current_selection if self._current_selection else self.default_value


class NumberInput(SettingsInput):
    """Input for numeric settings with validation."""

    def __init__(
        self,
        label_text: str,
        default_value: float | int,
        min_value: float | int | None = None,
        max_value: float | int | None = None,
        step: float | int | None = None,
        tooltip: str | None = None,
    ):
        """
        Initialize a number input.

        Args:
            label_text: Text for the input label
            default_value: Default numeric value
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            step: Step size for increment/decrement (optional)
            tooltip: Tooltip text to display (optional)
        """
        super().__init__(label_text, str(default_value))

        self._min_value: float | int | None = min_value
        self._max_value: float | int | None = max_value
        self._step: float | int | None = step
        self._is_int: bool = isinstance(default_value, int)

        # Create input
        self.number_input: TextInput = TextInput(
            value=str(default_value),
            style=Pack(flex=1, padding=5),
            on_change=self._handle_input_change,
        )
        self.input_container.insert(0, self.number_input)

        # Add tooltip if provided
        if tooltip:
            tooltip_label = Label(
                tooltip,
                style=Pack(
                    padding=(0, 5),
                    font_size=12,
                    font_style="italic",
                    color=COLORS["text_secondary"],
                ),
            )
            self.container.add(tooltip_label)

        # Add error label
        self.error_label: Label = Label(
            "",
            style=Pack(
                padding=(0, 5),
                font_size=12,
                font_style="italic",
                color=COLORS["danger"],
                visibility="hidden",
            ),
        )
        self.container.add(self.error_label)

    def _handle_input_change(self, widget: TextInput):
        """Handle changes to the input field."""
        try:
            # Try to convert input to number
            value = float(widget.value) if not self._is_int else int(widget.value)

            # Validate range
            if self._min_value is not None and value < self._min_value:
                raise ValueError(f"Value must be at least {self._min_value}")
            if self._max_value is not None and value > self._max_value:
                raise ValueError(f"Value must be at most {self._max_value}")

            # Clear error if validation passes
            self.error_label.text = ""
            self.error_label.style.visibility = "hidden"

            # Update modification status
            self.is_modified = str(value) != self.default_value
            self.reset_button.style.visibility = "visible" if self.is_modified else "hidden"

        except ValueError as e:
            # Show error message
            self.error_label.text = str(e)
            self.error_label.style.visibility = "visible"
            self.is_modified = True
            self.reset_button.style.visibility = "visible"

    def _do_reset(self):
        """Reset input to default value."""
        self.number_input.value = self.default_value
        self.is_modified = False
        self.reset_button.style.visibility = "hidden"
        self.error_label.style.visibility = "hidden"

    @property
    def value(self) -> float | int | None:
        """Get the current numeric value."""
        try:
            if self._is_int:
                return int(self.number_input.value)
            return float(self.number_input.value)
        except ValueError:
            return None


class BooleanInput(SettingsInput):
    """Input for boolean settings."""

    def __init__(
        self,
        label_text: str,
        default_value: bool,
        tooltip: str | None = None,
    ):
        """
        Initialize a boolean input.

        Args:
            label_text: Text for the input label
            default_value: Default boolean value
            tooltip: Tooltip text to display (optional)
        """
        super().__init__(label_text, str(default_value))

        # Create switch
        from toga import Switch
        self.switch: Switch = Switch(
            text="",
            value=default_value,
            style=Pack(padding=5),
            on_change=self._handle_switch_change,
        )
        self.input_container.insert(0, self.switch)

        # Add tooltip if provided
        if tooltip:
            tooltip_label = Label(
                tooltip,
                style=Pack(
                    padding=(0, 5),
                    font_size=12,
                    font_style="italic",
                    color=COLORS["text_secondary"],
                ),
            )
            self.container.add(tooltip_label)

    def _handle_switch_change(self, widget: Switch):
        """Handle changes to the switch."""
        self.is_modified = widget.value != (self.default_value.lower() == "true")
        self.reset_button.style.visibility = "visible" if self.is_modified else "hidden"

    def _do_reset(self):
        """Reset switch to default value."""
        self.switch.value = self.default_value.lower() == "true"
        self.is_modified = False
        self.reset_button.style.visibility = "hidden"

    @property
    def value(self) -> bool:
        """Get the current boolean value."""
        return self.switch.value


class SimpleSelectionInput(SettingsInput):
    """Simple selection input without categories."""

    def __init__(
        self,
        label_text: str,
        items: list[str],
        default_value: str,
        tooltip: str | None = None,
    ):
        """
        Initialize a simple selection input.

        Args:
            label_text: Text for the input label
            items: List of items to select from
            default_value: Default selected value
            tooltip: Tooltip text to display (optional)
        """
        super().__init__(label_text, default_value)

        # Create selection
        self.selection: Selection = Selection(
            items=items,
            value=default_value,
            style=Pack(flex=1),
            on_change=self._handle_selection_change,
        )
        self.input_container.insert(0, self.selection.container)

        # Add tooltip if provided
        if tooltip:
            tooltip_label = Label(
                tooltip,
                style=Pack(
                    padding=(0, 5),
                    font_size=12,
                    font_style="italic",
                    color=COLORS["text_secondary"],
                ),
            )
            self.container.add(tooltip_label)

    def _handle_selection_change(self, widget: Selection):
        """Handle changes to the selection."""
        if widget.value is None:
            return
        self.is_modified = str(widget.value) != self.default_value
        self.reset_button.style.visibility = "visible" if self.is_modified else "hidden"

    def _do_reset(self):
        """Reset selection to default value."""
        self.selection.value = self.default_value
        self.is_modified = False
        self.reset_button.style.visibility = "hidden"

    @property
    def value(self) -> str:
        """Get the current selection value."""
        return str(self.selection.value) if self.selection.value else self.default_value
