"""Optional Langfuse instrumentation for HLT-hosted GPT Researcher.

The upstream project already supports LangSmith through LangChain. This module is
the HLT overlay for cross-ecosystem Langfuse visibility. Keep it defensive: a
missing package or missing env vars must never break local research runs.
"""
from __future__ import annotations

from contextlib import contextmanager
import logging
import os
import sys
from typing import Any, Iterator

logger = logging.getLogger(__name__)

DEFAULT_LANGFUSE_BASE_URL = "https://us.cloud.langfuse.com"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def _base_url() -> str:
    return (
        os.getenv("LANGFUSE_BASE_URL")
        or os.getenv("LANGFUSE_HOST")
        or DEFAULT_LANGFUSE_BASE_URL
    )


def should_record_langfuse_io() -> bool:
    """Return whether prompts and outputs may be sent to Langfuse."""

    return _env_flag("LANGFUSE_RECORD_IO") or _env_flag("AI_SDK_TELEMETRY_RECORD_IO")


def is_langfuse_configured() -> bool:
    """Return whether the required Langfuse credentials are present."""

    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def get_langfuse_runtime_status() -> dict[str, Any]:
    """Return redacted Langfuse readiness suitable for /health responses."""

    package_available = True
    try:
        import langfuse  # noqa: F401
    except Exception:
        package_available = False

    return {
        "configured": is_langfuse_configured(),
        "package_available": package_available,
        "public_key": bool(os.getenv("LANGFUSE_PUBLIC_KEY")),
        "secret_key": bool(os.getenv("LANGFUSE_SECRET_KEY")),
        "base_url": _base_url(),
        "record_io": should_record_langfuse_io(),
    }


def _get_langfuse_client() -> Any | None:
    if not is_langfuse_configured():
        return None

    os.environ.setdefault("LANGFUSE_BASE_URL", _base_url())

    try:
        from langfuse import get_client
    except Exception as exc:
        logger.warning("Langfuse package is unavailable: %s", exc)
        return None

    try:
        return get_client()
    except Exception as exc:
        logger.warning("Langfuse client initialization failed: %s", exc)
        return None


@contextmanager
def observe_langfuse(
    *,
    name: str,
    as_type: str = "span",
    model: str | None = None,
    input: Any | None = None,
    metadata: dict[str, Any] | None = None,
    model_parameters: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    """Start a Langfuse observation if configured; otherwise yield no-op."""

    client = _get_langfuse_client()
    if client is None:
        yield None
        return

    try:
        manager = client.start_as_current_observation(
            name=name,
            as_type=as_type,
            model=model,
            input=input,
            metadata=metadata,
            model_parameters=model_parameters,
        )
        observation = manager.__enter__()
    except Exception as exc:
        logger.warning("Langfuse observation start failed: %s", exc)
        yield None
        return

    exc_info = (None, None, None)
    try:
        yield observation
    except BaseException:
        exc_info = sys.exc_info()
        raise
    finally:
        try:
            manager.__exit__(*exc_info)
        except Exception as exc:
            logger.warning("Langfuse observation close failed: %s", exc)


def update_observation(
    observation: Any | None,
    *,
    output: Any | None = None,
    metadata: dict[str, Any] | None = None,
    level: str | None = None,
    status_message: str | None = None,
) -> None:
    """Best-effort observation update that never affects the research path."""

    if observation is None:
        return

    try:
        observation.update(
            output=output,
            metadata=metadata,
            level=level,
            status_message=status_message,
        )
    except Exception as exc:
        logger.warning("Langfuse observation update failed: %s", exc)
