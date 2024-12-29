"""Settings dialog for configuring application preferences."""

from __future__ import annotations

import asyncio
import platform

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Dict, cast

from standalone_app.features.settings.constants import COLORS, STYLES
from standalone_app.features.settings.utils import create_section_label, toggle_visibility
from standalone_app.features.ui.components.selection import Selection
from standalone_app.features.ui.settings.inputs import APIKeyInput, BooleanInput, ModelSelectionInput, NumberInput, SimpleSelectionInput
from standalone_app.utils.api_providers import API_PROVIDERS, API_PROVIDERS_MANAGER
from toga import Box, Button, Divider, Label, ScrollContainer, Window
from toga.style import Pack
from toga.style.pack import COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from standalone_app.app import GPTResearcherApp
    from toga import Selection, Switch, Widget


class SettingsWindow(Window):
    """Settings window for configuring application preferences."""

    MIN_WIDTH: ClassVar[int] = 600
    MIN_HEIGHT: ClassVar[int] = 400
    MAX_WIDTH: ClassVar[int] = 1200
    MAX_HEIGHT: ClassVar[int] = 800
    PADDING: ClassVar[int] = 40 if platform.system() == "Darwin" else 50

    def __init__(
        self,
        app: GPTResearcherApp,
        on_save: Callable[[], None] | None = None,
        *args,
        resizable: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(*args, resizable=resizable, **kwargs)

        self.title: str = "Settings"
        self._parent_app: GPTResearcherApp = app
        self.on_save: Callable[[], None] | None = on_save
        self.api_inputs: dict[str, APIKeyInput] = {}

        # Load current settings
        self.current_settings: dict[str, str] = self._parent_app.settings_manager.settings

        # Create main container with flexible layout
        self.main_container: Box = Box(
            style=Pack(
                direction=COLUMN,
                padding=(5, 5),
                flex=1,
                background_color=COLORS["background"],
            )
        )

        # Create a ScrollContainer that expands to fill available space
        scroll_container = ScrollContainer(
            content=self.main_container,
            style=Pack(
                direction=COLUMN,
                padding=2,
                flex=1,
                background_color=COLORS["background"],
            ),
            horizontal=False,
            vertical=True,
        )

        # Set the window's content
        self.content: ScrollContainer = scroll_container

        # 1. Basic Settings Section
        basic_settings = Box(style=STYLES["card"])
        basic_settings.add(create_section_label("1. Choose Your Language"))
        basic_settings.add(
            Label(
                "Select the language you want the research to be written in:",
                style=Pack(padding=(2, 0), font_size=14),
            )
        )
        language_input = SimpleSelectionInput(
            "Language",
            ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
            "English",
            "Select the language you want the research to be written in",
        )
        self.language_input = language_input
        basic_settings.add(language_input.container)
        self.main_container.add(basic_settings)
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # 2. AI Model Selection
        model_settings = Box(style=STYLES["card"])
        model_settings.add(create_section_label("2. Choose Your AI Assistant"))

        free_providers = API_PROVIDERS_MANAGER.get_free_providers(include_setup_required=True)
        model_categories: dict[str, list[str]] = {
            "Free AI Models (No API Key Required)": [],
            "Trial Models (Free Account Required)": [],
            "Paid AI Models (API Key Required)": [],
        }
        for provider in free_providers:
            category = "Free AI Models (No API Key Required)" if not provider.get("setup_required") else "Trial Models (Free Account Required)"
            for model in provider.get("models", []):
                model_categories[category].append(f"{provider['name']}: {model}")

        paid_models: list[str] = [
            "OpenAI: gpt-4",
            "OpenAI: gpt-3.5-turbo",
            "Anthropic: claude-2",
            "Anthropic: claude-instant",
            "Google: palm-2",
            "Cohere: command",
        ]
        model_categories["Paid AI Models (API Key Required)"] = paid_models

        # Find first available model for default
        default_model: str | None = None
        for category in ["Trial Models (Free Account Required)", "Free AI Models (No API Key Required)"]:
            if model_categories[category]:
                default_model = model_categories[category][0]
                break
        if not default_model:
            default_model = "OpenAI: gpt-4"  # Fallback default

        # Create model selection with categories
        llm_input = ModelSelectionInput(
            "Select AI Model",
            model_categories,
            default_model,
        )
        self.llm_input: ModelSelectionInput = llm_input
        model_settings.add(llm_input.container)

        # Add rate limit note
        model_settings.add(
            Label(
                "\nNote: Free models have usage limits. The system will automatically switch to another free model if needed.",
                style=Pack(
                    padding=(2, 0),
                    font_size=12,
                    font_style="italic",
                ),
            )
        )
        self.main_container.add(model_settings)
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # Connect model selection to API visibility
        llm_input.model_selection.on_change = self._handle_model_change

        # 3. API Keys Section (if needed)
        self.api_settings: Box = self._create_api_settings()
        self.main_container.add(self.api_settings)
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # 4. Research Settings
        research_settings = self._create_research_settings()
        self.main_container.add(research_settings)
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # 5. Performance Settings
        performance_settings = self._create_performance_settings()
        self.main_container.add(performance_settings)
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # 6. Advanced Settings
        self.main_container.add(self._create_advanced_settings())
        self.main_container.add(Divider(style=Pack(padding=(5, 0))))

        # Status message
        self.status_label: Label = Label(
            "",
            style=Pack(
                padding=(5, 0),
                font_size=14,
                height=20,
                text_align="center",
                color=COLORS["text"],
            ),
        )
        self.main_container.add(self.status_label)

        # Add button box
        button_box = Box(
            style=Pack(
                direction=ROW,
                padding=(5, 0),
                alignment="center",
            )
        )

        self.save_button: Button = Button(
            "Save Settings",
            on_press=self._save_settings,
            style=STYLES["button_success"],
        )

        self.cancel_button: Button = Button(
            "Cancel",
            on_press=self._cancel,
            style=STYLES["button_danger"],
        )

        button_box.add(self.save_button)
        button_box.add(self.cancel_button)
        self.main_container.add(button_box)

    def _toggle_api_expander(
        self,
        widget: Switch,
    ) -> None:
        """Toggle the visibility of the additional APIs section."""
        toggle_visibility(self.additional_apis_box, widget)
        for api_input in self.api_inputs.values():
            if api_input.key_name in ["TAVILY_API_KEY", "OPENAI_API_KEY"]:
                continue
            api_input.style.visibility = "visible" if widget.value else "hidden"

    def _create_api_settings(self) -> Box:
        """Create the API settings section with required and optional APIs."""
        box = Box(style=STYLES["card"])

        # API Keys Section
        box.add(create_section_label("3. API Keys (Optional)"))
        box.add(Label("Only needed if you want to use paid AI models:", style=Pack(padding=(5, 0), font_size=14)))

        # Add API Key inputs
        self.api_inputs: dict[str, APIKeyInput] = {}

        # Add primary API inputs first
        for provider, details in API_PROVIDERS["required"].items():
            api_input = APIKeyInput(details["key_name"], details["display_name"], details["description"], provider)
            self.api_inputs[provider] = api_input
            box.add(api_input)

        # Create container for additional APIs with collapsed initial state
        self.additional_apis_box: Box = Box(
            style=Pack(
                direction=COLUMN,
                padding=0,
                height=0,
                visibility="hidden",
            )
        )
        del self.additional_apis_box.style.flex
        box.add(self.additional_apis_box)

        # Create all additional API inputs
        for provider, details in cast(Dict[str, Dict[str, Any]], API_PROVIDERS["optional"]).items():
            if provider == "tavily":
                continue
            api_input = APIKeyInput(details["key_name"], details["display_name"], details["description"], provider)
            self.api_inputs[provider] = api_input
            self.additional_apis_box.add(api_input)

        return box

    def _create_research_settings(self) -> Box:
        """Create the research settings section."""
        box = Box(style=STYLES["card"])
        box.add(create_section_label("4. Research Settings"))

        # Retriever selection
        self.retriever_input: SimpleSelectionInput = SimpleSelectionInput(
            "Search Engine",
            ["tavily", "google", "duckduckgo", "searchapi", "bing"],
            self.current_settings.get("RETRIEVER", "tavily"),
            "Choose which search engine to use for research",
        )
        box.add(self.retriever_input.container)

        # Report format selection
        self.report_format_input: SimpleSelectionInput = SimpleSelectionInput(
            "Report Format",
            ["APA", "MLA", "Chicago", "Harvard"],
            self.current_settings.get("REPORT_FORMAT", "APA"),
            "Choose the citation style for research reports",
        )
        box.add(self.report_format_input.container)

        # Max search results
        self.max_search_results_input: NumberInput = NumberInput(
            "Max Search Results Per Query",
            int(self.current_settings.get("MAX_SEARCH_RESULTS_PER_QUERY", "5")),
            min_value=1,
            max_value=20,
            tooltip="Maximum number of search results to process per query",
        )
        box.add(self.max_search_results_input.container)

        # Total words
        self.total_words_input: NumberInput = NumberInput(
            "Total Words",
            int(self.current_settings.get("TOTAL_WORDS", "1000")),
            min_value=100,
            max_value=10000,
            tooltip="Target word count for generated reports",
        )
        box.add(self.total_words_input.container)

        # Max iterations
        self.max_iterations_input: NumberInput = NumberInput(
            "Max Research Iterations",
            int(self.current_settings.get("MAX_ITERATIONS", "4")),
            min_value=1,
            max_value=10,
            tooltip="Maximum number of research iterations to perform",
        )
        box.add(self.max_iterations_input.container)

        # Max subtopics
        self.max_subtopics_input: NumberInput = NumberInput(
            "Max Subtopics",
            int(self.current_settings.get("MAX_SUBTOPICS", "3")),
            min_value=1,
            max_value=10,
            tooltip="Maximum number of subtopics to explore",
        )
        box.add(self.max_subtopics_input.container)

        # Curate sources
        self.curate_sources_input: BooleanInput = BooleanInput(
            "Curate Sources",
            self.current_settings.get("CURATE_SOURCES", "false").lower() == "true",
            "Filter and validate sources before using them",
        )
        box.add(self.curate_sources_input.container)

        return box

    def _create_performance_settings(self) -> Box:
        """Create the performance settings section."""
        box = Box(style=STYLES["card"])
        box.add(create_section_label("5. Performance Settings"))

        # Token limits
        self.fast_token_limit_input: NumberInput = NumberInput(
            "Fast LLM Token Limit",
            int(self.current_settings.get("FAST_TOKEN_LIMIT", "2000")),
            min_value=100,
            max_value=8000,
            tooltip="Maximum tokens for quick operations",
        )
        box.add(self.fast_token_limit_input.container)

        self.smart_token_limit_input: NumberInput = NumberInput(
            "Smart LLM Token Limit",
            int(self.current_settings.get("SMART_TOKEN_LIMIT", "4000")),
            min_value=100,
            max_value=8000,
            tooltip="Maximum tokens for complex operations",
        )
        box.add(self.smart_token_limit_input.container)

        self.strategic_token_limit_input: NumberInput = NumberInput(
            "Strategic LLM Token Limit",
            int(self.current_settings.get("STRATEGIC_TOKEN_LIMIT", "4000")),
            min_value=100,
            max_value=8000,
            tooltip="Maximum tokens for strategic decisions",
        )
        box.add(self.strategic_token_limit_input.container)

        # Browse chunk length
        self.browse_chunk_length_input: NumberInput = NumberInput(
            "Browse Chunk Length",
            int(self.current_settings.get("BROWSE_CHUNK_MAX_LENGTH", "8192")),
            min_value=1000,
            max_value=16000,
            tooltip="Maximum length of text chunks when processing web pages",
        )
        box.add(self.browse_chunk_length_input.container)

        # Summary token limit
        self.summary_token_limit_input: NumberInput = NumberInput(
            "Summary Token Limit",
            int(self.current_settings.get("SUMMARY_TOKEN_LIMIT", "700")),
            min_value=100,
            max_value=2000,
            tooltip="Maximum tokens for summary generation",
        )
        box.add(self.summary_token_limit_input.container)

        return box

    def _create_advanced_settings(self) -> Box:
        """Create the advanced settings section."""
        box = Box(style=STYLES["card"])
        box.add(create_section_label("6. Advanced Settings"))

        # Temperatures
        self.temperature_input: NumberInput = NumberInput(
            "Temperature",
            float(self.current_settings.get("TEMPERATURE", "0.4")),
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            tooltip="Creativity level for text generation (0.0 = focused, 2.0 = creative)",
        )
        box.add(self.temperature_input.container)

        self.llm_temperature_input: NumberInput = NumberInput(
            "LLM Temperature",
            float(self.current_settings.get("LLM_TEMPERATURE", "0.55")),
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            tooltip="Creativity level for LLM responses",
        )
        box.add(self.llm_temperature_input.container)

        # Similarity threshold
        self.similarity_threshold_input: NumberInput = NumberInput(
            "Similarity Threshold",
            float(self.current_settings.get("SIMILARITY_THRESHOLD", "0.42")),
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            tooltip="Threshold for determining text similarity (0.0 = different, 1.0 = identical)",
        )
        box.add(self.similarity_threshold_input.container)

        # Memory backend
        self.memory_backend_input: SimpleSelectionInput = SimpleSelectionInput(
            "Memory Backend",
            ["local", "redis", "pinecone"],
            self.current_settings.get("MEMORY_BACKEND", "local"),
            "Storage backend for research memory",
        )
        box.add(self.memory_backend_input.container)

        # Scraper
        self.scraper_input: SimpleSelectionInput = SimpleSelectionInput(
            "Web Scraper",
            ["bs", "playwright", "selenium"],
            self.current_settings.get("SCRAPER", "bs"),
            "Web scraping engine to use",
        )
        box.add(self.scraper_input.container)

        # User agent
        self.user_agent_input: SimpleSelectionInput = SimpleSelectionInput(
            "User Agent",
            [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            ],
            self.current_settings.get(
                "USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
            ),
            "Browser identification string to use when accessing websites",
        )
        box.add(self.user_agent_input.container)

        return box

    async def _validate_all_api_keys(self) -> bool:
        """Validate all API keys that have been entered."""
        self.status_label.text = "Validating API keys..."
        validation_tasks: list[Coroutine[Any, Any, bool]] = []

        for api_input in self.api_inputs.values():
            if api_input.input.value and api_input.input.value.strip():  # Only validate if a value is entered
                validation_tasks.append(api_input.validate_api_key())

        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        return all(isinstance(r, bool) and r for r in results)

    async def _save_settings(self, widget: Widget) -> None:
        """Save all settings to environment variables and config file."""
        self.save_button.enabled = False
        self.status_label.text = "Saving settings..."

        # Validate API keys
        if not await self._validate_all_api_keys():
            self.status_label.text = "Some API keys are invalid. Please check and try again."
            self.save_button.enabled = True
            return

        try:
            # Collect all settings
            settings: dict[str, str] = {}

            # Save API Keys
            for api_input in self.api_inputs.values():
                if api_input.input.value:  # Only save if value is not empty
                    settings[api_input.key_name] = api_input.input.value

            # Save Basic Settings
            settings["LANGUAGE"] = cast(str, self.language_input.value).lower()

            # Save Research Settings
            settings["RETRIEVER"] = self.retriever_input.value
            settings["REPORT_FORMAT"] = self.report_format_input.value
            settings["MAX_SEARCH_RESULTS_PER_QUERY"] = str(self.max_search_results_input.value)
            settings["TOTAL_WORDS"] = str(self.total_words_input.value)
            settings["MAX_ITERATIONS"] = str(self.max_iterations_input.value)
            settings["MAX_SUBTOPICS"] = str(self.max_subtopics_input.value)
            settings["CURATE_SOURCES"] = str(self.curate_sources_input.value).lower()

            # Save Performance Settings
            settings["FAST_TOKEN_LIMIT"] = str(self.fast_token_limit_input.value)
            settings["SMART_TOKEN_LIMIT"] = str(self.smart_token_limit_input.value)
            settings["STRATEGIC_TOKEN_LIMIT"] = str(self.strategic_token_limit_input.value)
            settings["BROWSE_CHUNK_MAX_LENGTH"] = str(self.browse_chunk_length_input.value)
            settings["SUMMARY_TOKEN_LIMIT"] = str(self.summary_token_limit_input.value)

            # Save Advanced Settings
            settings["TEMPERATURE"] = str(self.temperature_input.value)
            settings["LLM_TEMPERATURE"] = str(self.llm_temperature_input.value)
            settings["SIMILARITY_THRESHOLD"] = str(self.similarity_threshold_input.value)
            settings["MEMORY_BACKEND"] = self.memory_backend_input.value
            settings["SCRAPER"] = self.scraper_input.value
            settings["USER_AGENT"] = self.user_agent_input.value

            # Apply settings using settings_manager directly
            self._parent_app.settings_manager.save_settings(settings)
            self._parent_app.settings_manager.apply_settings(settings)

            self.status_label.text = "Settings saved successfully!"

            if self.on_save is not None:
                self.on_save()

            self.close()

        except Exception as e:
            self.status_label.text = f"Error saving settings: {str(e)}"
            self.save_button.enabled = True

        finally:
            self.save_button.enabled = True

    def _cancel(self, widget: Widget) -> None:
        """Close the window without saving."""
        self.close()

    def close(self):
        """Close the settings window."""
        super().close()

    def show(self) -> None:
        """Show the settings window with automatic sizing."""
        # First show the window to let widgets calculate their sizes
        super().show()

        # Let the layout engine process
        self.main_container.refresh()

        # Set initial size to minimum dimensions
        self.size = (self.MIN_WIDTH, self.MIN_HEIGHT)

        # Let the layout engine process again with the new size
        self.main_container.refresh()

        # Calculate final window size within constraints
        window_width = max(self.MIN_WIDTH, min(self.main_container.layout.content_width + self.PADDING, self.MAX_WIDTH))
        window_height = max(self.MIN_HEIGHT, min(self.main_container.layout.content_height + self.PADDING, self.MAX_HEIGHT))

        # Set the final window size
        self.size = (window_width, window_height)

    def _handle_model_change(self, widget: Selection) -> None:
        """Handle changes to model selection to show/hide API inputs."""
        if not widget.value:
            return

        show_apis: bool = "Paid" in str(self.llm_input.category_selection.value)
        visibility: str = "visible" if show_apis else "hidden"

        # Update container style
        if show_apis:
            self.additional_apis_box.style.update(
                visibility=visibility,
                padding=(5, 0),
                flex=1,
            )
            del self.additional_apis_box.style.height
        else:
            self.additional_apis_box.style.update(
                visibility=visibility,
                height=0,
                padding=0,
            )
            del self.additional_apis_box.style.flex

        # Update visibility of individual inputs
        for api_input in self.api_inputs.values():
            if api_input.key_name == "TAVILY_API_KEY":
                continue
            api_input.style.visibility = visibility

        # Force layout refresh
        self.additional_apis_box.refresh()
        self.main_container.refresh()
