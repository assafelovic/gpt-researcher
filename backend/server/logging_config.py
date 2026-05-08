"""Compatibility shim for research logging configuration.

The canonical implementation lives in
`gpt_researcher.utils.logging_config`. This module keeps the backend import
path stable while sharing the same artifact directory and handler behavior.
"""

from gpt_researcher.utils.logging_config import (
    JSONResearchHandler,
    get_json_handler,
    get_research_logger,
    setup_research_logging,
)

__all__ = [
    "JSONResearchHandler",
    "get_json_handler",
    "get_research_logger",
    "setup_research_logging",
]
