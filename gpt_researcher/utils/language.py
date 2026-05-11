"""Language helpers for localized report output."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_GERMAN_LANGUAGE_ALIASES = {
    "de",
    "de-at",
    "de-ch",
    "de-de",
    "deutsch",
    "german",
}

_SOURCE_TITLE_NOISE_PATTERNS = (
    re.compile(r"(?i)\blearn\b.*\bmore\b"),
    re.compile(r"(?i)\bapp\s*&\s*ai coding\b"),
    re.compile(r"(?i)\bgame design\b"),
    re.compile(r"(?i)\bbecome a pro coder\b"),
    re.compile(r"(?i)\bdon't miss\b"),
    re.compile(r"(?i)\bfew free spots left\b"),
    re.compile(r"(?i)\bapply now\b"),
    re.compile(r"(?i)\bentry-challenge\b"),
)

_GERMAN_TECHNICAL_REPLACEMENTS = (
    (
        re.compile(
            r"(?i)\b(?P<left>[A-Za-z0-9À-ÿ][A-Za-z0-9À-ÿ.+:/_-]*(?:\s+[A-Za-z0-9À-ÿ][A-Za-z0-9À-ÿ.+:/_-]*){0,4})"
            r"\s+vs\.?\s+"
            r"(?P<right>[A-Za-z0-9À-ÿ][A-Za-z0-9À-ÿ.+:/_-]*(?:\s+[A-Za-z0-9À-ÿ][A-Za-z0-9À-ÿ.+:/_-]*){0,4})\b"
        ),
        lambda match: f"{match.group('left')} gegenüber {match.group('right')}",
    ),
    (re.compile(r"(?i)\bbest practices\b"), "bewährte Vorgehensweisen"),
    (re.compile(r"(?i)\bbest practice\b"), "bewährte Vorgehensweise"),
    (re.compile(r"(?i)\bopen source\b"), "Open-Source"),
    (re.compile(r"(?i)\buse cases\b"), "Anwendungsfälle"),
    (re.compile(r"(?i)\buse case\b"), "Anwendungsfall"),
    (re.compile(r"(?i)\btrade[-\s]?offs\b"), "Abwägungen"),
    (re.compile(r"(?i)\btrade[-\s]?off\b"), "Abwägung"),
    (re.compile(r"(?i)\bstate of the art\b"), "Stand der Technik"),
    (re.compile(r"(?i)\bend[-\s]?to[-\s]?end\b"), "Ende-zu-Ende"),
    (re.compile(r"(?i)\broadmap\b"), "Fahrplan"),
)


def normalize_language_name(language: str | None) -> str:
    """Normalize a language label to a compact lowercase key."""
    if not language:
        return ""
    return re.sub(r"[\s_]+", "-", str(language).strip().lower())


def is_german_language(language: str | None) -> bool:
    """Return True when the configured language points to German."""
    normalized = normalize_language_name(language)
    if not normalized:
        return False
    return normalized in _GERMAN_LANGUAGE_ALIASES or normalized.startswith("de-")


def _source_host(source_url: str | None) -> str:
    if not source_url:
        return ""
    parsed = urlparse(str(source_url))
    host = (parsed.netloc or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def looks_like_source_title_noise(text: str | None) -> bool:
    """Return True when a title looks like boilerplate or marketing noise."""
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return False

    lower = normalized.lower()
    if any(pattern.search(lower) for pattern in _SOURCE_TITLE_NOISE_PATTERNS):
        return True

    if len(normalized) <= 140 and normalized.count(",") >= 2:
        if "learn" in lower or "coding" in lower or "more" in lower:
            return True

    return False


def normalize_source_title(title: str | None, source_url: str | None = None) -> str:
    """Return a cleaner display title for a source."""
    normalized = re.sub(r"\s+", " ", str(title or "")).strip(" \t\r\n-–—|:;")
    if not normalized:
        return _source_host(source_url)

    if looks_like_source_title_noise(normalized):
        return _source_host(source_url)

    return normalized


def strip_source_boilerplate(text: str | None) -> str:
    """Remove leading promotional title lines from source content."""
    if not text:
        return ""

    content = re.sub(r"\r\n?", "\n", str(text)).strip()
    if not content:
        return ""

    while content:
        first_line, newline, remainder = content.partition("\n")
        candidate = first_line.strip()
        if not candidate:
            content = remainder.lstrip()
            continue

        sentence = candidate
        sentence_match = re.match(r"^(.*?[.!?])\s*(.*)$", candidate)
        if sentence_match:
            sentence = sentence_match.group(1).strip()
            line_remainder = sentence_match.group(2).strip()
        else:
            line_remainder = ""

        if not looks_like_source_title_noise(sentence):
            break

        if newline:
            content = remainder.lstrip()
        else:
            content = line_remainder

    return re.sub(r"\n{3,}", "\n\n", content).strip()


def _normalize_german_prose_segment(text: str) -> str:
    normalized = text
    for pattern, replacement in _GERMAN_TECHNICAL_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)

    normalized = re.sub(r"(?<=[A-Za-zÄÖÜäöüß])\s*-\s*(?=[A-Za-zÄÖÜäöüß])", "-", normalized)
    normalized = re.sub(r"\s+([,.;:!?])", r"\1", normalized)
    return normalized


def _normalize_german_markdown_line(line: str) -> str:
    parts: list[str] = []
    index = 0

    while index < len(line):
        backtick_index = line.find("`", index)
        if backtick_index == -1:
            parts.append(_normalize_german_prose_segment(line[index:]))
            break

        parts.append(_normalize_german_prose_segment(line[index:backtick_index]))

        tick_count = 1
        while backtick_index + tick_count < len(line) and line[backtick_index + tick_count] == "`":
            tick_count += 1

        delimiter = "`" * tick_count
        closing_index = line.find(delimiter, backtick_index + tick_count)
        if closing_index == -1:
            parts.append(line[backtick_index:])
            break

        parts.append(line[backtick_index : closing_index + tick_count])
        index = closing_index + tick_count

    return "".join(parts)


def normalize_german_technical_terms(text: str | None) -> str:
    """Smooth common English technical loanwords in German prose."""
    if not text:
        return ""

    content = re.sub(r"\r\n?", "\n", str(text))
    normalized_lines: list[str] = []
    in_fenced_code_block = False
    fence_marker = ""

    for line in content.splitlines(keepends=True):
        fence_match = re.match(r"^(\s*)(`{3,}|~{3,})", line)
        if fence_match:
            marker = fence_match.group(2)
            if in_fenced_code_block and fence_marker and marker[0] == fence_marker[0] and len(marker) >= len(fence_marker):
                in_fenced_code_block = False
                fence_marker = ""
            else:
                in_fenced_code_block = True
                fence_marker = marker
            normalized_lines.append(line)
            continue

        if in_fenced_code_block:
            normalized_lines.append(line)
            continue

        normalized_lines.append(_normalize_german_markdown_line(line))

    return "".join(normalized_lines)
