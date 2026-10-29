"""
Report parsing: Markdown text -> sections, paragraphs, citations, evidence.
-------------------------------------------------------------------------
The writer emits plain Markdown. Parsing happens at scoring time (the archive
keeps only the original text) with Python-Markdown, which the repo already
depends on, plus its tables extension; malformed input is left to the library
to tolerate.

Output (see eval-design/infrastructure.md §4):

  title           first level-1 heading
  references      URLs listed under a trailing References/Sources heading; a
                  claim by the report, not necessarily what the body cites
  parse_warnings  format problems, input to the instruction-following metric
  sections[]      heading_path + paragraphs[]
    paragraphs[]  type text | list | table | quote | code, plain text,
                  citations (links the paragraph makes) and evidence (the
                  retrieved chunks behind each cited URL; found=false means
                  the report cites a URL that was never retrieved)
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import markdown

from .archive import normalize_url

_REFERENCES_HEADING = re.compile(r"^\s*(references|sources|citations|bibliography|参考(文献|资料)?)\s*:?\s*$", re.I)
_BARE_URL = re.compile(r"https?://[^\s\)\]\,\"'<>]+")
_BLOCK_TYPES = {"p": "text", "ul": "list", "ol": "list", "table": "table",
                "blockquote": "quote", "pre": "code"}
_HEADINGS = {f"h{i}": i for i in range(1, 7)}


class _Blocks(HTMLParser):
    """Flattens Python-Markdown's HTML into top-level blocks with their links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._depth = 0
        self._cur: dict | None = None
        self._href: str | None = None
        self._anchor: list[str] = []

    def handle_starttag(self, tag, attrs):
        if self._depth == 0:
            self._cur = {"tag": tag, "text": [], "links": []}
        self._depth += 1
        if self._cur is None:
            return
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._anchor = []
        elif tag in ("li", "tr", "br") and self._cur["text"]:
            self._cur["text"].append("\n")
        elif tag in ("td", "th"):
            self._cur["text"].append(" | ")

    def handle_startendtag(self, tag, attrs):
        if self._cur is not None and tag == "br":
            self._cur["text"].append("\n")

    def handle_endtag(self, tag):
        if self._cur is not None and tag == "a" and self._href:
            self._cur["links"].append({"url": self._href, "anchor": "".join(self._anchor).strip()})
            self._href = None
        self._depth = max(0, self._depth - 1)
        if self._depth == 0 and self._cur is not None:
            self._cur["text"] = re.sub(r"[ \t]+", " ", "".join(self._cur["text"])).strip()
            self.blocks.append(self._cur)
            self._cur = None

    def handle_data(self, data):
        if self._depth == 0:
            if data.strip():
                self.blocks.append({"tag": "p", "text": data.strip(), "links": []})
            return
        if self._cur is not None:
            self._cur["text"].append(data)
            if self._href is not None:
                self._anchor.append(data)


def _citations(block: dict) -> list[dict]:
    out, seen = [], set()
    for link in block["links"]:
        url = link["url"]
        if url.startswith(("http://", "https://")) and url not in seen:
            seen.add(url)
            out.append({"url": url, "anchor": link["anchor"]})
    for url in _BARE_URL.findall(block["text"]):
        url = url.rstrip(".;:")
        if url not in seen:
            seen.add(url)
            out.append({"url": url, "anchor": ""})
    return out


def parse_report(markdown_text: str, chunks_by_url: dict[str, list[str]] | None = None) -> dict:
    """Parse a report. `chunks_by_url` (normalised URL -> chunk ids) fills `evidence`."""
    chunks_by_url = chunks_by_url or {}
    html = markdown.markdown(markdown_text or "", extensions=["tables"])
    parser = _Blocks()
    parser.feed(html)
    parser.close()

    warnings: list[str] = []
    title = None
    references: list[str] = []
    sections: list[dict] = []
    path: list[tuple[int, str]] = []
    in_refs = False
    last_level = 0
    current: dict | None = None
    saw_refs = False

    def new_section() -> dict:
        sec = {"section_id": f"sec{len(sections) + 1}",
               "heading_path": [t for _, t in path], "paragraphs": []}
        sections.append(sec)
        return sec

    for block in parser.blocks:
        tag = block["tag"]
        if tag in _HEADINGS:
            level, text = _HEADINGS[tag], block["text"]
            if last_level and level > last_level + 1:
                _add(warnings, "heading_level_jump")
            last_level = level
            if level == 1:
                if title is None:
                    title = text
                else:
                    _add(warnings, "multiple_titles")
            in_refs = bool(_REFERENCES_HEADING.match(text))
            if in_refs:
                saw_refs = True
                current = None
                continue
            while path and path[-1][0] >= level:
                path.pop()
            path.append((level, text))
            current = None
            continue
        if tag == "hr":
            continue
        cites = _citations(block)
        if in_refs:
            references.extend(c["url"] for c in cites if c["url"] not in references)
            continue
        if not block["text"]:
            continue
        if current is None:
            if not path:
                _add(warnings, "content_before_first_heading")
            current = new_section()
        para_id = f"{current['section_id']}-p{len(current['paragraphs']) + 1}"
        current["paragraphs"].append({
            "para_id": para_id,
            "type": _BLOCK_TYPES.get(tag, "text"),
            "text": block["text"],
            "citations": cites,
            "evidence": [
                {"url": c["url"],
                 "found": normalize_url(c["url"]) in chunks_by_url,
                 "chunk_ids": list(chunks_by_url.get(normalize_url(c["url"]), []))}
                for c in cites
            ],
        })

    if title is None:
        _add(warnings, "no_title")
    if not saw_refs:
        _add(warnings, "no_references_section")
    elif not references:
        _add(warnings, "references_without_links")

    return {"title": title, "references": references,
            "parse_warnings": warnings, "sections": sections}


def _add(warnings: list[str], w: str) -> None:
    if w not in warnings:
        warnings.append(w)


def body_paragraphs(parsed: dict) -> list[dict]:
    return [p for s in parsed["sections"] for p in s["paragraphs"]]


def cited_urls(parsed: dict) -> list[str]:
    """Distinct URLs cited in the body (not the references list)."""
    seen, out = set(), []
    for p in body_paragraphs(parsed):
        for c in p["citations"]:
            key = normalize_url(c["url"])
            if key not in seen:
                seen.add(key)
                out.append(c["url"])
    return out


_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+|\n+")
_MD_LINK_TAIL = re.compile(r"\(\s*https?://[^)]*\)")


def report_sentences(parsed: dict) -> list[str]:
    """Body sentences, with URLs removed, for matching chunks against the text."""
    out = []
    for p in body_paragraphs(parsed):
        text = _BARE_URL.sub("", _MD_LINK_TAIL.sub("", p["text"]))
        for s in _SENTENCE_END.split(text):
            s = s.strip(" |-*")
            if len(s) >= 20:
                out.append(s)
    return out
