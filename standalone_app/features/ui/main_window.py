"""Main window component for the GPT Researcher application."""

from __future__ import annotations

from typing import TYPE_CHECKING

import loguru

from standalone_app.features.research.controller import ResearchController
from standalone_app.features.settings.constants import APP_STYLES, COLORS
from standalone_app.features.ui.components.buttons import ActionButtons
from standalone_app.features.ui.components.onboarding import OnboardingOverlay
from standalone_app.features.ui.sections.input import InputSection
from standalone_app.features.ui.sections.options import OptionsSection
from standalone_app.features.ui.sections.previous_research import PreviousResearchPanel
from standalone_app.features.ui.sections.results import ResultsSection
from standalone_app.features.ui.sections.status import StatusSection
from standalone_app.features.ui.settings.dialog import SettingsWindow
from standalone_app.utils.file_controller import FileController
from toga import Box, Label, MainWindow, ScrollContainer, SplitContainer
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from standalone_app.app import GPTResearcherApp
    from toga import Widget

logger = loguru.logger


class ResearcherWindow(MainWindow):
    """Main window component for the GPT Researcher application."""

    def __init__(
        self,
        app: GPTResearcherApp,
    ):
        """Initialize the main window."""
        super().__init__(title=app.formal_name)
        self.size: tuple[int, int] = (900, 700)

        # Initialize controllers
        self.research_controller: ResearchController = ResearchController(app)
        self.file: FileController = FileController(self)

        # Initialize UI components
        self.main_box: Box = self._create_main_box()
        self.input_section: InputSection = self._create_input_section()
        self.options_section: OptionsSection = self._create_options_section()
        self.status_section: StatusSection = self._create_status_section()
        self.results_section: ResultsSection = self._create_results_section()
        self.action_buttons: ActionButtons = self._create_action_buttons()

        # Create split container
        split_container = SplitContainer(
            style=Pack(
                flex=1,
                direction=COLUMN,
            )
        )

        # Create previous research panel
        self.previous_research: PreviousResearchPanel = PreviousResearchPanel()

        # Create scroll container for main content
        scroll_container = ScrollContainer(
            content=self.main_box,
            horizontal=False,
            vertical=True,
            style=Pack(flex=1),
        )
        split_container.content = (
            (self.previous_research.panel_container, 1),
            (scroll_container, 4),
        )

        # Create onboarding overlay
        self.onboarding: OnboardingOverlay = OnboardingOverlay(self)

        # Set window content and show
        self.content: SplitContainer = split_container
        self.show()

        # Show onboarding on first launch
        self.onboarding.start()

    def _create_main_box(self) -> Box:
        """Create the main container box."""
        main_box = Box(style=APP_STYLES["main_container"])

        # Create header with app title
        header_label = Label(
            "Autonomous Researcher",
            style=Pack(
                font_size=28,
                font_weight="bold",
                padding=(0, 0, 20, 0),
                color=COLORS["text"],
                alignment=CENTER,
            ),
        )
        main_box.add(header_label)

        return main_box

    def _create_input_section(self) -> InputSection:
        """Create and add input section."""
        input_section = InputSection(on_research=self.handle_research, on_settings=self.show_settings)
        self.main_box.add(input_section.input_container)
        return input_section

    def _create_options_section(self) -> OptionsSection:
        """Create and add options section."""
        options_section = OptionsSection()
        self.main_box.add(options_section.options_box)
        return options_section

    def _create_status_section(self) -> StatusSection:
        """Create and add status section."""
        status_section = StatusSection()
        self.main_box.add(status_section.status_box)
        return status_section

    def _create_results_section(self) -> ResultsSection:
        """Create and add results section."""
        results_section = ResultsSection()
        self.main_box.add(results_section.results_container)
        return results_section

    def _create_action_buttons(self) -> ActionButtons:
        """Create and add action buttons."""
        action_buttons = ActionButtons(
            on_copy=self.handle_copy,
            on_download_md=self.handle_download_md,
            on_download_pdf=self.handle_download_pdf,
            on_download_docx=self.handle_download_docx,
            on_download_json=self.handle_download_json,
        )
        self.main_box.add(action_buttons.action_box)
        return action_buttons

    def show_settings(self, widget: Widget | None = None):
        """Show the settings window."""
        from standalone_app.app import GPTResearcherApp

        assert isinstance(self.app, GPTResearcherApp)
        settings_window = SettingsWindow(self.app, on_save=self.handle_settings_save)
        settings_window.show()

    def handle_settings_save(self):
        """Handle settings save event."""
        # Save research settings
        settings = {}
        settings["REPORT_FORMAT"] = str(self.options_section.format_input.value)
        settings["TEMPERATURE"] = self.options_section.temp_input.value
        settings["TOTAL_WORDS"] = self.options_section.words_input.value

        # Apply settings using settings_manager
        from standalone_app.app import GPTResearcherApp

        assert isinstance(self.app, GPTResearcherApp)
        self.app.settings_manager.save_settings(settings)
        self.app.settings_manager.apply_settings(settings)

        self.status_section.set_status("Settings saved successfully", "success")

    async def handle_research(
        self,
        widget: Widget | None = None,
    ):
        """Handle research button press."""
        query = self.input_section.get_query()
        if not query:
            self.status_section.set_status("Please enter a research query", "warning")
            return

        # Disable input during research
        self.input_section.disable_input()
        self.status_section.set_status("Researching...", "text_secondary")
        self.results_section.clear_results()
        self.action_buttons.update_button_states(False)

        try:
            # Get search engine and API key
            search_engine = self.options_section.get_search_engine()
            tavily_api_key = None
            if search_engine.lower() == "tavily":
                tavily_api_key = self.options_section.get_tavily_api_key()
                if not tavily_api_key:
                    self.status_section.set_status("Please enter your Tavily API key", "warning")
                    return

            # Conduct research
            report = await self.research_controller.start_research(
                query=query,
                report_type=self.options_section.get_report_type(),
                tone=self.options_section.get_tone(),
                source=self.options_section.get_source(),
                curate_sources=self.options_section.get_curate_sources(),
                search_engine=search_engine,
                num_sources=self.options_section.get_num_sources(),
                tavily_api_key=tavily_api_key,
            )

            # Update UI with results
            self.results_section.set_results(report)
            self.status_section.set_status("Research complete", "success")
            self.action_buttons.update_button_states(True)

            # Add to previous research panel
            self.previous_research.add_research_item(query=query, report_type=self.options_section.get_report_type())

        except Exception as e:
            logger.exception("Error during research")
            self.status_section.set_status("An error occurred", "danger")
            self.results_section.set_results(f"An error occurred: {str(e)}")
            self.action_buttons.update_button_states(False)

        finally:
            # Re-enable input
            self.input_section.enable_input()

    async def handle_copy(self, widget: Widget | None = None):
        """Handle copy to clipboard button press."""
        results = self.results_section.get_results()
        if results:
            success = await self.file.copy_to_clipboard(results)
            if success:
                self.status_section.set_status("Copied to clipboard", "success")
            else:
                self.status_section.set_status("Error copying to clipboard", "danger")

    async def handle_download_md(self, widget: Widget | None = None):
        """Handle download as markdown button press."""
        results = self.results_section.get_results()
        if results:
            path = await self.file.save_markdown(results)
            if path:
                self.status_section.set_status("Report saved as Markdown", "success")
            else:
                self.status_section.set_status("Error saving file", "danger")

    async def handle_download_pdf(self, widget: Widget | None = None):
        """Handle download as PDF button press."""
        results = self.results_section.get_results()
        if results:
            path = await self.file.save_pdf(results)
            if path:
                self.status_section.set_status("Report saved as PDF", "success")
            else:
                self.status_section.set_status("PDF export not yet implemented", "warning")

    async def handle_download_docx(self, widget: Widget | None = None):
        """Handle download as DOCX button press."""
        results = self.results_section.get_results()
        if results:
            path = await self.file.save_docx(results)
            if path:
                self.status_section.set_status("Report saved as DOCX", "success")
            else:
                self.status_section.set_status("DOCX export not yet implemented", "warning")

    async def handle_download_json(self, widget: Widget | None = None):
        """Handle download log button press."""
        if self.research_controller.researcher:
            research_data = self.research_controller.get_research_data()
            costs = research_data.get("costs", 0)
            sources = research_data.get("sources", [])
            path = await self.file.save_json_log(
                query=self.input_section.get_query(),
                report_type=self.options_section.get_report_type(),
                tone=self.options_section.get_tone().name,
                source=self.options_section.get_source(),
                costs=float(costs) if isinstance(costs, (int, float)) else 0,
                sources=sources if isinstance(sources, list) else [],
            )
            if path:
                self.status_section.set_status("Log saved as JSON", "success")
            else:
                self.status_section.set_status("Error saving log", "danger")
