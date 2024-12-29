"""Settings management utilities."""

from __future__ import annotations

import json
import loguru
import os

from typing import TYPE_CHECKING

from gpt_researcher.config import Config as GPTConfig

if TYPE_CHECKING:
    from standalone_app.app import GPTResearcherApp

logger = loguru.logger


class SettingsManager:
    """Manages application settings."""

    def __init__(
        self,
        app: GPTResearcherApp,
    ):
        self.app: GPTResearcherApp = app
        self.settings: dict[str, str] = {}
        self.config: GPTConfig | None = None
        self.load_settings()

    def load_settings(self) -> dict[str, str]:
        """Load settings from config file first, then fall back to environment variables."""
        settings: dict[str, str] = {}
        config_path = self.app.paths.config / "settings.json"

        # First try to load from config file
        try:
            if config_path.exists():
                settings.update(json.loads(config_path.read_text()))
        except Exception:
            logger.exception("Error loading settings from '%s'", config_path)

        # Then fill in any missing settings from environment variables
        env_vars = [
            "OPENAI_API_KEY",
            "TAVILY_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "BING_API_KEY",
            "SEARCHAPI_API_KEY",
            "SERPAPI_API_KEY",
            "SERPER_API_KEY",
            "EXA_API_KEY",
            "NCBI_API_KEY",
            "LANGCHAIN_API_KEY",
            "COHERE_API_KEY",
            "PERPLEXITY_API_KEY",
            "HUGGINGFACE_API_KEY",
            "METAPHOR_API_KEY",
            "YOU_API_KEY",
            "BROWSERLESS_API_KEY",
            "PRODIA_API_KEY",
            "ARXIV_API_KEY",
            "LANGUAGE",
            "REPORT_FORMAT",
            "SMART_LLM",
            "TEMPERATURE",
            "RETRIEVER",
            "MAX_SEARCH_RESULTS_PER_QUERY",
            "TOTAL_WORDS",
            "CURATE_SOURCES",
            "EMBEDDING",
            "SIMILARITY_THRESHOLD",
            "FAST_LLM",
            "STRATEGIC_LLM",
            "FAST_TOKEN_LIMIT",
            "SMART_TOKEN_LIMIT",
            "STRATEGIC_TOKEN_LIMIT",
            "BROWSE_CHUNK_MAX_LENGTH",
            "SUMMARY_TOKEN_LIMIT",
            "LLM_TEMPERATURE",
            "USER_AGENT",
            "MEMORY_BACKEND",
            "MAX_ITERATIONS",
            "AGENT_ROLE",
            "SCRAPER",
            "MAX_SUBTOPICS",
            "REPORT_SOURCE",
            "DOC_PATH",
        ]

        for key in env_vars:
            # Only use environment variable if setting isn't already defined
            value = os.environ.get(key)
            if key not in settings and value:
                settings[key] = value

        self.settings = settings

        # Initialize gpt-researcher config
        config_file = config_path if config_path.exists() else None
        self.config = GPTConfig(str(config_file) if config_file else None)

        return settings

    def save_settings(
        self,
        settings: dict[str, str],
    ) -> None:
        """Save settings to config file and update gpt-researcher config."""
        config_path = self.app.paths.config / "settings.json"

        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save to our settings file
            config_path.write_text(json.dumps(settings, indent=2))

            # Update environment variables to affect gpt-researcher config
            for key, value in settings.items():
                os.environ[key] = str(value)

            # Reinitialize gpt-researcher config with new settings
            self.config = GPTConfig(str(config_path))
        except OSError:
            logger.exception(
                "The config file is not writable, please check permissions: '%s'",
                config_path,
            )

        except Exception:
            logger.exception("Error saving settings")

    def apply_settings(
        self,
        new_settings: dict[str, str],
    ):
        """Apply settings to the app, environment, and gpt-researcher config."""
        # Update settings dict
        self.settings.update(new_settings)

        # Apply settings where needed
        # This replaces environment variables
        for key, value in new_settings.items():
            # Update environment variables for API keys and config
            os.environ[key] = str(value)

        # Save settings to file and reinitialize config
        self.save_settings(new_settings)

    def get_config(self) -> GPTConfig:
        """Get the current gpt-researcher config instance."""
        if not self.config:
            config_path = self.app.paths.config / "settings.json"
            if config_path.exists():
                self.config = GPTConfig(str(config_path))
            else:
                self.config = GPTConfig()
        return self.config
