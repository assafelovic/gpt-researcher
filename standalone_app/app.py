"""Main application module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from toga import App

from standalone_app.features.settings.storage import SettingsManager
from standalone_app.features.ui.main_window import ResearcherWindow
from standalone_app.utils.logging import get_logger, setup_logging

if TYPE_CHECKING:
    import loguru


class GPTResearcherApp(App):
    """Main application class."""

    def __init__(self):
        super().__init__(
            formal_name="Autonomous Researcher",
            app_id="org.autonomousresearcher",
            app_name="Autonomous Researcher",
        )
        self.logger: loguru.Logger = get_logger(__name__)

        # Setup logging
        self.app_logs_dir: Path = Path(self.paths.data) / "logs"
        self.app_logs_dir.mkdir(parents=True, exist_ok=True)
        setup_logging(self.app_logs_dir)
        self.logger.info("Application starting up...")
        self.logger.debug("App data directory: {}", self.app_logs_dir)

        # Use the existing SettingsManager
        self.settings_manager: SettingsManager = SettingsManager(self)
        self.logger.info("Settings manager initialized")

    def startup(self):
        """Initialize the main application window."""
        self.logger.info("Creating main window...")
        self.main_window: ResearcherWindow = ResearcherWindow(self)
        self.main_window.show()
        self.logger.info("Main window created and displayed")


def main() -> GPTResearcherApp:
    """Create and return the main application instance."""
    return GPTResearcherApp()


if __name__ == "__main__":
    app = main()
    app.main_loop()
