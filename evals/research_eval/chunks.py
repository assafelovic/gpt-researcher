"""
Splitting a sub-query's context string back into source chunks.
--------------------------------------------------------------
`_process_sub_query` returns one string: the selected chunks rendered by
`PromptFamily.pretty_print_docs`, i.e. repeated blocks of

    Source: <url>
    Title: <title>
    Content: <text>

This module undoes that rendering so the archive can store each chunk once and
let spans refer to it by id. Text that does not follow the format (MCP results,
the Granite prompt families) is kept as a single chunk with `url = None` and
flagged, rather than silently dropped.
"""

from __future__ import annotations

import hashlib
import re

_DOC_HEADER = re.compile(r"^Source: (?P<url>[^\n]*)\nTitle: (?P<title>[^\n]*)\nContent: ", re.M)


def chunk_id(url: str | None, content: str) -> str:
    """Stable id from the chunk's source and text, so repeats share one entry."""
    h = hashlib.sha1(f"{url or ''}\n{content}".encode("utf-8")).hexdigest()
    return "c" + h[:12]


def split_context(text: str) -> tuple[list[dict], list[str]]:
    """Parse a rendered context string into chunks.

    Returns (chunks, warnings). Each chunk is {id, url, title, content}.
    """
    if not text or not str(text).strip():
        return [], []
    text = str(text)
    warnings: list[str] = []
    chunks: list[dict] = []
    matches = list(_DOC_HEADER.finditer(text))

    lead = text[:matches[0].start()] if matches else text
    if lead.strip():
        warnings.append("unattributed_text" if matches else "unrecognised_context_format")
        content = lead.strip()
        chunks.append({"id": chunk_id(None, content), "url": None, "title": None,
                       "content": content})

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[m.end():end].strip()
        url = m.group("url").strip() or None
        title = m.group("title").strip()
        title = None if title in ("", "None") else title
        chunks.append({"id": chunk_id(url, content), "url": url, "title": title,
                       "content": content})
    return chunks, warnings
