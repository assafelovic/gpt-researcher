"""Optional, failure-isolated research lifecycle events.

The core researcher deliberately does not interpret or persist these events.
Consumers can provide either a callable or an object exposing ``on_event``.
Observer failures must never change research results.
"""

import inspect
import logging
from collections.abc import Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ResearchObserver(Protocol):
    """Object-style observer accepted by :class:`GPTResearcher`."""

    def on_event(self, event: str, **fields: Any) -> Any: ...


async def emit_research_event(
    observer: ResearchObserver | Callable[..., Any] | None,
    event: str,
    **fields: Any,
) -> None:
    """Notify an observer without allowing telemetry to affect research."""
    if observer is None:
        return

    try:
        handler = getattr(observer, "on_event", observer)
        result = handler(event, **fields)
        if inspect.isawaitable(result):
            await result
    except Exception as exc:  # noqa: BLE001 - observers must never affect research
        logger.debug("Research observer failed for %s: %s", event, type(exc).__name__)
