"""Options section component for the GPT Researcher application."""

from __future__ import annotations

from gpt_researcher.utils.enum import Tone
from standalone_app.features.settings.constants import STYLES
from standalone_app.features.ui.components.selection import Selection
from standalone_app.features.ui.settings.inputs import APIKeyInput
from standalone_app.features.ui.settings.types import TextInputSettings
from toga import Box, Label, Switch, TextInput
from toga.style import Pack


class OptionsSection:
    """Research options section for selecting report type, tone, and source."""

    def __init__(self):
        """Initialize the options section."""
        self._create_options_section()

    def _create_options_section(self):
        """Create the research options section."""
        self.options_box: Box = Box(style=STYLES["card"])

        # Research Configuration Section (Collapsible)
        research_header = Box(style=STYLES["row"])
        research_header.add(Label("Research Configuration", style=STYLES["section_label"]))
        self.research_switch: Switch = Switch("", value=True, on_change=self._toggle_research)
        research_header.add(self.research_switch)
        self.options_box.add(research_header)

        self.research_section: Box = Box(style=STYLES["section"])

        # Report type selection
        report_type_box = Box(style=STYLES["row"])
        report_type_box.add(Label("Report Type:", style=STYLES["label"]))
        self.report_type_select: Selection = Selection(
            items=["Summary - Short and fast (~2 min)", "Detailed - In depth and longer (~5 min)", "Resource Report"],
            style=STYLES["selection"],
        )
        report_type_box.add(self.report_type_select.container)
        self.research_section.add(report_type_box)

        # Report Format
        format_box = Box(style=STYLES["row"])
        format_box.add(Label("Report Format:", style=STYLES["label"]))
        self.format_input: Selection = Selection(
            items=[
                "APA",
                "MLA",
                "Chicago",
                "Harvard",
                "IEEE",
            ],
            value="Chicago",
            style=STYLES["selection"],
        )
        format_box.add(self.format_input.container)
        self.research_section.add(format_box)

        # Tone selection
        tone_box = Box(style=STYLES["row"])
        tone_box.add(Label("Tone:", style=STYLES["label"]))
        self.tone_select: Selection = Selection(
            items=[tone.name for tone in Tone],  # Use enum names
            style=STYLES["selection"],
        )
        tone_box.add(self.tone_select.container)
        self.research_section.add(tone_box)

        # Source selection
        source_box = Box(style=STYLES["row"])
        source_box.add(Label("Source:", style=STYLES["label"]))
        self.source_select: Selection = Selection(
            items=["The Web", "My Documents", "Hybrid"],
            style=STYLES["selection"],
        )
        source_box.add(self.source_select.container)
        self.research_section.add(source_box)

        self.options_box.add(self.research_section)
        self.options_box.add(Box(style=STYLES["divider"]))

        # Source Configuration Section (Collapsible)
        source_header = Box(style=STYLES["row"])
        source_header.add(Label("Source Configuration", style=STYLES["section_label"]))
        self.source_switch: Switch = Switch("", value=True, on_change=self._toggle_source)
        source_header.add(self.source_switch)
        self.options_box.add(source_header)

        self.source_section: Box = Box(style=STYLES["section"])

        # Source Quality
        source_quality_box = Box(style=STYLES["row"])
        source_quality_box.add(Label("Source Quality:", style=STYLES["label"]))
        self.curate_input: Switch = Switch(
            "Carefully check and filter sources",
            value=False,
            style=Pack(height=25),
        )
        source_quality_box.add(self.curate_input)
        self.source_section.add(source_quality_box)

        # Search Engine
        search_engine_box = Box(style=STYLES["row"])
        search_engine_box.add(Label("Search Engine:", style=STYLES["label"]))

        # Create a box for engine selection and Tavily API key
        engine_input_box = Box(style=STYLES["input_group"])

        self.engine_select: Selection = Selection(
            items=[
                "duckduckgo (No API needed)",
                "tavily (Recommended)",
                "google",
                "bing",
                "searchapi",
                "serper",
                "metaphor",
                "you",
            ],
            style=Pack(
                width=300,  # Fixed width for selection
                padding=2,
                height=35,
            ),
            on_change=self._handle_engine_change,
        )
        engine_input_box.add(self.engine_select.container)

        # Tavily API Key
        self.tavily_input: APIKeyInput = APIKeyInput(
            key_name="TAVILY_API_KEY",
            display_name="Tavily API Key",
            tooltip="Required for Tavily search. Get your API key from tavily.com",
            provider_key="tavily",
        )
        self.options_box.add(self.tavily_input)

        # Initialize visibility before adding to layout
        self._handle_engine_change(self.engine_select)
        engine_input_box.add(self.tavily_input)
        search_engine_box.add(engine_input_box)
        self.source_section.add(search_engine_box)

        # Number of sources
        num_sources_box = Box(style=STYLES["row"])
        num_sources_box.add(
            Label(
                "Number of Sources:",
                style=Pack(
                    padding=(2, 0),
                    font_size=14,
                    flex=1,
                ),
            )
        )
        self.num_sources_input: TextInput = TextInput(
            value="5",
            placeholder="3-10",
            style=STYLES["input"],
        )
        num_sources_box.add(self.num_sources_input)
        self.source_section.add(num_sources_box)

        self.options_box.add(self.source_section)
        self.options_box.add(Box(style=STYLES["divider"]))

        # Advanced Settings Section (Collapsible)
        advanced_header = Box(style=STYLES["row"])
        advanced_header.add(Label("Advanced Settings", style=STYLES["section_label"]))
        self.advanced_switch = Switch("", value=False, on_change=self._toggle_advanced)
        advanced_header.add(self.advanced_switch)
        self.options_box.add(advanced_header)

        self.advanced_section: Box = Box(style=STYLES["section"])

        # Research Length
        words_input = TextInputSettings(
            "Word Count",
            "1000",
            "Suggested: 500-2000 words",
        )
        self.words_input: TextInput = words_input.input
        self.advanced_section.add(
            Label(
                "Research Length:",
                style=Pack(
                    padding=(2, 0),
                    font_size=14,
                ),
            )
        )
        self.advanced_section.add(words_input.container)

        # AI Creativity
        temp_input = TextInputSettings(
            "Creativity Level",
            "0.4",
            "0.0 (Factual) to 1.0 (Creative)",
        )
        self.temp_input: TextInput = temp_input.input
        self.advanced_section.add(
            Label(
                "AI Creativity Level:",
                style=Pack(
                    padding=(5, 0, 2, 0),
                    font_size=14,
                ),
            )
        )
        self.advanced_section.add(
            Label(
                "Temperature controls how creative the AI is. Lower values (closer to 0) make it more focused and factual. Higher values (closer to 1) make it more creative.",
                style=Pack(
                    padding=(2, 0),
                    font_size=12,
                ),
            )
        )
        self.advanced_section.add(temp_input.container)

        # Initially hidden
        self.advanced_section.style.update(visibility="hidden", height=0)
        self.options_box.add(self.advanced_section)

    def _toggle_section(self, section: Box, switch: Switch) -> None:
        """Toggle visibility of a section."""
        if switch.value:
            section.style.update(visibility="visible")
            del section.style.height
        else:
            section.style.update(visibility="hidden", height=0)
        section.refresh()
        self.options_box.refresh()

    def _toggle_research(self, widget: Switch) -> None:
        """Toggle research section visibility."""
        self._toggle_section(self.research_section, widget)

    def _toggle_source(self, widget: Switch) -> None:
        """Toggle source section visibility."""
        self._toggle_section(self.source_section, widget)

    def _toggle_advanced(self, widget: Switch) -> None:
        """Toggle advanced section visibility."""
        self._toggle_section(self.advanced_section, widget)

    def _handle_engine_change(self, widget: Selection):
        """Handle changes to the engine selection."""
        show_tavily = "tavily" in str(widget.value).lower()
        self.tavily_input.style.visibility = "visible" if show_tavily else "hidden"
        self.tavily_input.refresh()
        self.options_box.refresh()

    def get_report_type(self) -> str:
        """Get the selected report type."""
        assert self.report_type_select is not None
        assert isinstance(self.report_type_select.value, str)
        return self.report_type_select.value

    def get_tone(self) -> Tone:
        """Get the selected tone."""
        if self.tone_select is None or self.tone_select.value is None:
            return Tone.Objective
        if isinstance(self.tone_select.value, str):
            return Tone[self.tone_select.value]
        if isinstance(self.tone_select.value, Tone):
            return self.tone_select.value
        return Tone.Objective

    def get_source(self) -> str:
        """Get the selected source."""
        assert self.source_select is not None
        assert isinstance(self.source_select.value, str)
        return self.source_select.value

    def get_curate_sources(self) -> bool:
        """Get whether sources should be curated."""
        assert self.curate_input is not None
        return self.curate_input.value

    def get_search_engine(self) -> str:
        """Get the selected search engine."""
        assert self.engine_select is not None
        assert isinstance(self.engine_select.value, str)
        return self.engine_select.value.split(" (")[0]  # Remove any notes in parentheses

    def get_num_sources(self) -> int:
        """Get the number of sources."""
        assert self.num_sources_input is not None
        try:
            return int(self.num_sources_input.value)
        except (ValueError, TypeError):
            return 5  # Default value

    def get_tavily_api_key(self) -> str | None:
        """Get the Tavily API key."""
        if not self.tavily_input.input.value:
            return None
        return self.tavily_input.input.value.strip()

    def get_options(self) -> dict[str, str]:
        """Get the current options."""
        return {
            "engine": str(self.engine_select.value),
            "tone": str(self.tone_select.value),
            "report_type": str(self.report_type_select.value),
            "report_format": str(self.format_input.value),
            "word_count": str(self.words_input.value),
            "temperature": str(self.temp_input.value),
            "tavily_api_key": str(self.tavily_input.input.value),
        }
