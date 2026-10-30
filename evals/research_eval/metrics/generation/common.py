"""Helpers the generation metrics share: the report as text for a judge."""

from __future__ import annotations

import re

from ...archive import RunArchive
from ...report_parser import REFERENCES_HEADING, body_paragraphs

REPORT_CHARS = 60000     # the whole default / detailed report; deep reports are cut
_URL = re.compile(r"https?://\S+")
_MD_LINK = re.compile(r"\[([^\]]*)\]\(\s*https?://[^)\s]*\s*\)")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_BLANKS = re.compile(r"\n{3,}")


def paragraph_plain(p: dict) -> str:
    return _URL.sub("", p["text"]).strip()


def report_text(archive: RunArchive, limit: int = REPORT_CHARS) -> tuple[str, bool]:
    """Report body as the reader sees it (no references, no URLs). Returns (text, truncated).

    Built from the original Markdown rather than the parsed sections, so the
    judge sees the report's own structure: tables stay tables, a heading with
    only sub-headings under it is kept, and the title appears once. Links keep
    their anchor text; the References section is dropped.
    """
    lines, skip_level = [], 0
    for line in archive.report_markdown.splitlines():
        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            if skip_level and level > skip_level:
                continue
            skip_level = level if REFERENCES_HEADING.match(m.group(2).strip()) else 0
        if skip_level:
            continue
        lines.append(_URL.sub("", _MD_LINK.sub(r"\1", line)).rstrip())
    text = _BLANKS.sub("\n\n", "\n".join(lines)).strip()
    if len(text) <= limit:
        return text, False
    return text[:limit] + "\n\n[... report truncated ...]", True


def batches(items: list, size_of, limit: int) -> list[list]:
    """Split items into consecutive batches whose total size stays under limit."""
    out, cur, used = [], [], 0
    for it in items:
        n = size_of(it)
        if cur and used + n > limit:
            out.append(cur)
            cur, used = [], 0
        cur.append(it)
        used += n
    if cur:
        out.append(cur)
    return out


_CJK = re.compile(r"[㐀-鿿豈-﫿]")
_LATIN_WORD = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")


def word_count(text: str) -> int:
    """Latin words plus CJK characters (a CJK character is roughly a word)."""
    return len(_LATIN_WORD.findall(text)) + len(_CJK.findall(text))


def body_word_count(archive: RunArchive) -> int:
    return sum(word_count(paragraph_plain(p)) for p in body_paragraphs(archive.report))
