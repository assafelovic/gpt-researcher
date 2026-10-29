"""Helpers the generation metrics share: the report as text for a judge."""

from __future__ import annotations

import re

from ...archive import RunArchive
from ...report_parser import body_paragraphs

REPORT_CHARS = 60000     # the whole default / detailed report; deep reports are cut
_URL = re.compile(r"https?://\S+")


def paragraph_plain(p: dict) -> str:
    return _URL.sub("", p["text"]).strip()


def report_text(archive: RunArchive, limit: int = REPORT_CHARS) -> tuple[str, bool]:
    """Report body (headings + paragraphs, no references, no URLs). Returns (text, truncated)."""
    parsed = archive.report
    lines = [f"# {parsed['title']}"] if parsed.get("title") else []
    for sec in parsed["sections"]:
        if sec["heading_path"]:
            lines.append("#" * (len(sec["heading_path"]) + 1) + " " + sec["heading_path"][-1])
        lines.extend(paragraph_plain(p) for p in sec["paragraphs"])
    text = "\n\n".join(lines)
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
