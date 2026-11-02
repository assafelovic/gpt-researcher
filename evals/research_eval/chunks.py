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

# A title can span lines (some pages have line breaks in <title>); it never
# runs into the next block's "Source:" line.
_DOC_HEADER = re.compile(r"^Source: (?P<url>[^\n]*)\nTitle: (?P<title>(?:(?!\nSource: )[\s\S]){0,2000}?)"
                         r"\nContent: ", re.M)


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


def resplit_archived(chunks: dict[str, dict], spans: list[dict]) -> tuple[dict, list[dict], int]:
    """Repair archives captured before multi-line titles were parsed.

    A block whose title spanned lines was not recognised, so its URL, title and
    content were swallowed by the chunk before it: that URL looks never
    retrieved and its text is credited to the previous page. Each archived
    chunk is rendered back to its block and split again; spans' chunk_ids are
    rewritten to the pieces. Returns (chunks, spans, chunks split).
    """
    remap: dict[str, list[str]] = {}
    new_pieces: list[dict] = []
    for cid, ch in chunks.items():
        if "\nSource: " not in ch["content"]:
            continue
        text = (f"Source: {ch['url']}\nTitle: {ch.get('title') or ''}\nContent: {ch['content']}"
                if ch.get("url") else ch["content"])
        pieces, _ = split_context(text)
        if len(pieces) > 1:
            remap[cid] = [p["id"] for p in pieces]
            new_pieces.extend(pieces)
    if not remap:
        return chunks, spans, 0
    out = {cid: ch for cid, ch in chunks.items() if cid not in remap}
    for p in new_pieces:
        out.setdefault(p["id"], {"url": p["url"], "title": p["title"], "content": p["content"],
                                 "jev_score": None})
    new_spans = []
    for s in spans:
        ids = s.get("attributes", {}).get("chunk_ids")
        if ids and any(c in remap for c in ids):
            fixed = list(dict.fromkeys(n for c in ids for n in remap.get(c, [c])))
            s = {**s, "attributes": {**s["attributes"], "chunk_ids": fixed}}
        new_spans.append(s)
    return out, new_spans, len(remap)
