"""Shared helpers for parsing malformed JSON-like LLM responses.

These utilities provide the central repair path for code-fenced, quoted, or
line-based model output across actions, skills, and selectors.
"""

from __future__ import annotations

import json
import re
from typing import Any

import json_repair


def strip_model_wrappers(response: str | None) -> str:
    if not response:
        return ""

    cleaned = response.strip()
    cleaned = re.sub(r"^```(?:json|JSON)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_json_fragment(
    response: str | None,
    open_char: str = "{",
    close_char: str = "}",
) -> str | None:
    if not response:
        return None

    for candidate in (response, strip_model_wrappers(response)):
        if not candidate:
            continue
        start = candidate.find(open_char)
        end = candidate.rfind(close_char)
        if start == -1 or end == -1 or end <= start:
            continue
        return candidate[start : end + 1]

    return None


def quote_unquoted_object_keys(text: str) -> str:
    return re.sub(r'(?m)(^|[{\[,]\s*)([A-Za-z_][\w-]*)\s*:', r'\1"\2":', text)


def _add_candidate(candidates: list[str], seen: set[str], candidate: str | None) -> None:
    if not candidate:
        return

    normalized = candidate.strip()
    if not normalized or normalized in seen:
        return

    seen.add(normalized)
    candidates.append(normalized)


def _build_candidates(response: str | None, expected_kind: str) -> list[str]:
    cleaned = strip_model_wrappers(response)
    if not cleaned:
        return []

    candidates: list[str] = []
    seen: set[str] = set()

    _add_candidate(candidates, seen, response)
    _add_candidate(candidates, seen, cleaned)

    if cleaned[0] not in "{[":
        if expected_kind in {"object", "any"}:
            _add_candidate(candidates, seen, f"{{{cleaned}}}")
        if expected_kind in {"array", "any"}:
            _add_candidate(candidates, seen, f"[{cleaned}]")

    quoted_keys = quote_unquoted_object_keys(cleaned)
    _add_candidate(candidates, seen, quoted_keys)
    if quoted_keys and quoted_keys[0] not in "{[":
        if expected_kind in {"object", "any"}:
            _add_candidate(candidates, seen, f"{{{quoted_keys}}}")
        if expected_kind in {"array", "any"}:
            _add_candidate(candidates, seen, f"[{quoted_keys}]")

    if expected_kind in {"object", "any"}:
        _add_candidate(candidates, seen, extract_json_fragment(cleaned, "{", "}"))
    if expected_kind in {"array", "any"}:
        _add_candidate(candidates, seen, extract_json_fragment(cleaned, "[", "]"))

    return candidates


def _coerce_jsonish_value(value: str) -> Any:
    stripped = value.strip().rstrip(",").strip()
    if not stripped:
        return ""

    if stripped[0] in "{[\"'" or stripped.lower() in {"true", "false", "null"} or re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
        for loader in (json_repair.loads, json.loads):
            try:
                return loader(stripped)
            except Exception:
                continue

    return stripped.strip('"').strip("'")


def _bracket_delta(text: str) -> int:
    return sum(1 for char in text if char in "[{") - sum(1 for char in text if char in "]}")


def _parse_key_value_object(response: str) -> dict[str, Any] | None:
    lines = response.splitlines()
    parsed: dict[str, Any] = {}
    current_key: str | None = None
    current_value_lines: list[str] = []
    current_container_depth = 0
    saw_key = False

    def flush_current() -> None:
        nonlocal current_key, current_value_lines, current_container_depth
        if current_key is None:
            return
        parsed[current_key] = _coerce_jsonish_value("\n".join(current_value_lines))
        current_key = None
        current_value_lines = []
        current_container_depth = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current_key is not None and current_value_lines:
                current_value_lines.append("")
            continue

        if current_key is not None and current_container_depth > 0:
            current_value_lines.append(line)
            current_container_depth += _bracket_delta(line)
            continue

        match = re.match(r'^(?:["\']?)([A-Za-z_][\w-]*)(?:["\']?)\s*[:=]\s*(.*)$', line)
        if match:
            flush_current()
            current_key = match.group(1)
            current_value_lines = [match.group(2)]
            current_container_depth = _bracket_delta(match.group(2))
            saw_key = True
            continue

        if current_key is not None:
            current_value_lines.append(line)

    flush_current()
    return parsed if saw_key and parsed else None


def parse_llm_json_response(response: str | object | None, expected_kind: str = "object") -> Any | None:
    """Parse a JSON-ish LLM response into a dict or list.

    Args:
        response: Raw LLM response or already-parsed JSON object.
        expected_kind: "object", "array", or "any".
    """
    if response is None:
        return None

    if isinstance(response, dict):
        return response if expected_kind in {"object", "any"} else None
    if isinstance(response, list):
        return response if expected_kind in {"array", "any"} else None

    if expected_kind in {"object", "any"} and isinstance(response, str):
        cleaned = strip_model_wrappers(response)
        if cleaned and "\n" in cleaned and cleaned[0] not in "{[":
            kv_payload = _parse_key_value_object(cleaned)
            if kv_payload is not None:
                return kv_payload

    candidates = _build_candidates(response, expected_kind)
    for candidate in candidates:
        for loader in (json_repair.loads, json.loads):
            try:
                parsed = loader(candidate)
            except Exception:
                continue

            if expected_kind == "object" and not isinstance(parsed, dict):
                continue
            if expected_kind == "array" and not isinstance(parsed, list):
                continue
            if expected_kind == "any" and not isinstance(parsed, (dict, list)):
                continue

            return parsed

    if expected_kind in {"object", "any"} and isinstance(response, str):
        kv_payload = _parse_key_value_object(strip_model_wrappers(response))
        if kv_payload is not None:
            return kv_payload

    return None
