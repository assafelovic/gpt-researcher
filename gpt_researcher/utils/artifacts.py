from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone


def sanitize_artifact_component(value: str, fallback: str = "artifact") -> str:
    """Return a filesystem-friendly component."""
    cleaned = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    cleaned = re.sub(r"[\s-]+", "_", cleaned).strip("_")
    return cleaned or fallback


def make_unique_artifact_stem(prefix: str, label: str = "") -> str:
    """Build a collision-resistant artifact stem.

    The unique timestamp and UUID are placed before the label so that later
    truncation still preserves uniqueness.
    """
    safe_prefix = sanitize_artifact_component(prefix)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    nonce = uuid.uuid4().hex[:8]
    parts = [safe_prefix, timestamp, nonce]

    if label:
        parts.append(sanitize_artifact_component(label)[:40])

    return "_".join(parts)


def sanitize_filename(filename: str) -> str:
    """Compatibility helper for older call sites."""
    return sanitize_artifact_component(filename)
