"""Deterministic, offline citation provenance verification for Markdown reports.

Extracts cited HTTP(S) URLs from a generated Markdown report (ignoring fenced
code blocks, inline code spans, and embedded images) and compares them against
the sources actually visited or retrieved during research.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Common analytics/tracking query parameters that do not identify a distinct source.
_TRACKING_QUERY_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "dclid",
        "gbraid",
        "wbraid",
        "mc_cid",
        "mc_eid",
        "msclkid",
        "igshid",
    }
)

# Matches fenced code blocks (``` or ~~~), inline code spans (`...`), or prose.
_FENCED_CODE_RE = re.compile(
    r"(^|\n)([ \t]{0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?(?:\n[ \t]{0,3}\3[ \t]*(?=\n|$)|\Z))"
)
_INLINE_CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1", re.DOTALL)

# Reference-style link definitions: [label]: https://example.com "optional title"
_REF_DEF_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[[^\]]+\]:[ \t]*<?(https?://[^\s>]+)>?"
)

# Autolinks <https://...> and bare HTTP(S) URLs in prose.
_AUTOLINK_RE = re.compile(r"<(https?://[^\s<>]+)>")
_BARE_URL_RE = re.compile(r"https?://[^\s<>\"']+")

_TRAILING_PUNCT = ".,;:!?'\"`>]"


@dataclass(frozen=True)
class CitationAudit:
    """Structured result of verifying a report's citations against known sources."""

    cited_urls: list[str]
    verified_urls: list[str]
    unverified_urls: list[str]
    uncited_sources: list[str]
    verification_rate: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize the audit result to a plain JSON-compatible dictionary."""
        return {
            "cited_urls": list(self.cited_urls),
            "verified_urls": list(self.verified_urls),
            "unverified_urls": list(self.unverified_urls),
            "uncited_sources": list(self.uncited_sources),
            "verification_rate": self.verification_rate,
        }


def normalize_citation_url(url: str) -> str:
    """Return a canonical comparison key for an HTTP(S) URL.

    Normalizes scheme/hostname case, trailing DNS root dot, default ports
    (:80/:443), fragments, trailing slashes, analytics tracking parameters, and
    query parameter ordering without modifying meaningful path or query values.
    """
    if not isinstance(url, str):
        return ""
    raw = url.strip()
    if not raw:
        return ""

    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https") or not parsed.hostname:
        return raw

    host = parsed.hostname.lower().rstrip(".")
    try:
        port = parsed.port
    except ValueError:
        port = None

    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    if port is None or (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        netloc = host
    else:
        netloc = f"{host}:{port}"

    path = parsed.path or ""
    if path == "/":
        path = ""
    elif path.endswith("/"):
        path = path.rstrip("/")

    filtered_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_QUERY_PARAMS
    ]
    filtered_query.sort()
    query = urlencode(filtered_query, doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))


def _trim_bare_url(url: str) -> str:
    """Strip trailing sentence punctuation while preserving balanced parentheses."""
    cleaned = url.rstrip(_TRAILING_PUNCT)
    while cleaned.endswith(")") and cleaned.count(")") > cleaned.count("("):
        cleaned = cleaned[:-1].rstrip(_TRAILING_PUNCT)
    return cleaned


def _split_code_and_prose(markdown_text: str) -> list[tuple[bool, str]]:
    """Split Markdown into ``(is_code, segment)`` tuples preserving exact text."""
    segments: list[tuple[bool, str]] = []
    pos = 0
    for match in _FENCED_CODE_RE.finditer(markdown_text):
        prefix = match.group(1)
        code_start = match.start() + len(prefix)
        if code_start > pos:
            segments.extend(_split_inline_code(markdown_text[pos:code_start]))
        segments.append((True, markdown_text[code_start : match.end()]))
        pos = match.end()
    if pos < len(markdown_text):
        segments.extend(_split_inline_code(markdown_text[pos:]))
    return segments


def _split_inline_code(text: str) -> list[tuple[bool, str]]:
    segments: list[tuple[bool, str]] = []
    pos = 0
    for match in _INLINE_CODE_RE.finditer(text):
        if match.start() > pos:
            segments.append((False, text[pos : match.start()]))
        segments.append((True, match.group(0)))
        pos = match.end()
    if pos < len(text):
        segments.append((False, text[pos:]))
    return segments


def _iter_inline_links(prose: str) -> list[tuple[int, int, str, bool]]:
    """Find inline Markdown links/images as ``(start, end, url, is_image)``.

    Handles balanced parentheses inside URLs (e.g. Wikipedia links), optional
    angle-bracket destinations, and optional link titles.
    """
    matches: list[tuple[int, int, str, bool]] = []
    n = len(prose)
    i = 0
    while i < n:
        bracket_start = prose.find("[", i)
        if bracket_start == -1:
            break
        is_image = bracket_start > 0 and prose[bracket_start - 1] == "!"
        # Find closing ']' (ignore nested brackets cleanly).
        depth = 0
        j = bracket_start
        while j < n:
            ch = prose[j]
            if ch == "\\":
                j += 2
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n or depth != 0 or j + 1 >= n or prose[j + 1] != "(":
            i = bracket_start + 1
            continue

        # Parse destination inside (...), allowing balanced parens in URLs.
        dest_start = j + 2
        k = dest_start
        paren_depth = 1
        while k < n and paren_depth > 0:
            ch = prose[k]
            if ch == "\\":
                k += 2
                continue
            if ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    break
            k += 1
        if paren_depth != 0:
            i = j + 1
            continue

        raw_dest = prose[dest_start:k].strip()
        url = ""
        if raw_dest.startswith("<"):
            close_angle = raw_dest.find(">")
            if close_angle != -1:
                url = raw_dest[1:close_angle].strip()
        elif raw_dest:
            url = raw_dest.split()[0]

        span_start = bracket_start - 1 if is_image else bracket_start
        span_end = k + 1
        if url.lower().startswith(("http://", "https://")):
            matches.append((span_start, span_end, url, is_image))
        i = span_end

    return matches


def extract_cited_urls(report_markdown: str) -> list[str]:
    """Extract unique HTTP(S) URLs cited in a Markdown report in order of appearance.

    Fenced code blocks, inline code spans, and Markdown image links
    (``![alt](url)``) are ignored.
    """
    if not isinstance(report_markdown, str) or not report_markdown.strip():
        return []

    found: list[str] = []
    seen: set[str] = set()

    def _add(url: str) -> None:
        cleaned = url.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            found.append(cleaned)

    for is_code, segment in _split_code_and_prose(report_markdown):
        if is_code:
            continue

        # Mask inline link and image spans so bare URL scanning won't re-extract them.
        chars = list(segment)
        for start, end, url, is_image in _iter_inline_links(segment):
            if not is_image:
                _add(url)
            for idx in range(start, end):
                chars[idx] = " "
        remainder = "".join(chars)

        for match in _REF_DEF_RE.finditer(remainder):
            _add(_trim_bare_url(match.group(1)))
        remainder = _REF_DEF_RE.sub(" ", remainder)

        for match in _AUTOLINK_RE.finditer(remainder):
            _add(_trim_bare_url(match.group(1)))
        remainder = _AUTOLINK_RE.sub(" ", remainder)

        for match in _BARE_URL_RE.finditer(remainder):
            _add(_trim_bare_url(match.group(0)))

    return found


def _collect_known_sources(
    visited_urls: Iterable[str] | None,
    research_sources: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    """Build a mapping of ``normalized_url -> representative_original_url``."""
    known: dict[str, str] = {}

    def _register(url: Any) -> None:
        if not isinstance(url, str) or not url.strip():
            return
        norm = normalize_citation_url(url)
        if norm and norm not in known:
            known[norm] = url.strip()

    if visited_urls is not None:
        for url in visited_urls:
            _register(url)

    if research_sources is not None:
        for source in research_sources:
            if isinstance(source, Mapping):
                _register(source.get("url") or source.get("href"))

    return known


def verify_report_citations(
    report_markdown: str,
    visited_urls: Iterable[str] | None,
    research_sources: Iterable[Mapping[str, Any]] | None = None,
) -> CitationAudit:
    """Verify URLs cited in ``report_markdown`` against retrieved research sources.

    Args:
        report_markdown: Generated Markdown report text.
        visited_urls: Iterable of URLs visited during research.
        research_sources: Optional iterable of source metadata dicts (supporting
            ``url`` and ``href`` keys).

    Returns:
        A :class:`CitationAudit` containing verified citations, unverified
        (potentially hallucinated) citations, uncited sources, and the
        verification rate.
    """
    cited_urls = extract_cited_urls(report_markdown)
    known = _collect_known_sources(visited_urls, research_sources)

    verified_urls: list[str] = []
    unverified_urls: list[str] = []
    matched_known_keys: set[str] = set()

    for url in cited_urls:
        norm = normalize_citation_url(url)
        if norm in known:
            verified_urls.append(url)
            matched_known_keys.add(norm)
        else:
            unverified_urls.append(url)

    uncited_sources = sorted(
        original for norm, original in known.items() if norm not in matched_known_keys
    )
    verification_rate = (
        len(verified_urls) / len(cited_urls) if cited_urls else 1.0
    )

    return CitationAudit(
        cited_urls=cited_urls,
        verified_urls=verified_urls,
        unverified_urls=unverified_urls,
        uncited_sources=uncited_sources,
        verification_rate=verification_rate,
    )


def annotate_unverified_citations(
    report_markdown: str,
    visited_urls: Iterable[str] | None,
    research_sources: Iterable[Mapping[str, Any]] | None = None,
    label: str = "unverified",
) -> str:
    """Append a marker after unverified inline Markdown links without altering code or images.

    Args:
        report_markdown: Generated Markdown report text.
        visited_urls: Iterable of URLs visited during research.
        research_sources: Optional iterable of source metadata dicts.
        label: Marker text appended as `` [<label>]`` after unverified links.

    Returns:
        The annotated Markdown report string.
    """
    if not isinstance(report_markdown, str) or not report_markdown:
        return "" if report_markdown is None else str(report_markdown)

    known = _collect_known_sources(visited_urls, research_sources)
    marker = f" [{label}]"
    output_parts: list[str] = []

    for is_code, segment in _split_code_and_prose(report_markdown):
        if is_code:
            output_parts.append(segment)
            continue

        links = _iter_inline_links(segment)
        if not links:
            output_parts.append(segment)
            continue

        cursor = 0
        for start, end, url, is_image in links:
            output_parts.append(segment[cursor:end])
            cursor = end
            if is_image:
                continue
            if normalize_citation_url(url) not in known:
                if not segment[end:].startswith(marker):
                    output_parts.append(marker)
        output_parts.append(segment[cursor:])

    return "".join(output_parts)
