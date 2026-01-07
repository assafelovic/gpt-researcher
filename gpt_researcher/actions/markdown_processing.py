import re
import markdown
from typing import List, Dict

def extract_headers(markdown_text: str) -> List[Dict]:
    """
    Extract headers from markdown text.

    Args:
        markdown_text (str): The markdown text to process.

    Returns:
        List[Dict]: A list of dictionaries representing the header structure.
    """
    headers = []
    parsed_md = markdown.markdown(markdown_text)
    lines = parsed_md.split("\n")

    stack = []
    for line in lines:
        if line.startswith("<h") and len(line) > 2 and line[2].isdigit():
            level = int(line[2])
            header_text = line[line.index(">") + 1 : line.rindex("<")]

            while stack and stack[-1]["level"] >= level:
                stack.pop()

            header = {
                "level": level,
                "text": header_text,
            }
            if stack:
                stack[-1].setdefault("children", []).append(header)
            else:
                headers.append(header)

            stack.append(header)

    return headers

def extract_sections(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extract all written sections from subtopic report.

    Args:
        markdown_text (str): Subtopic report text.

    Returns:
        List[Dict[str, str]]: List of sections, each section is a dictionary containing
        'section_title' and 'written_content'.
    """
    sections = []
    parsed_md = markdown.markdown(markdown_text)
    
    pattern = r'<h\d>(.*?)</h\d>(.*?)(?=<h\d>|$)'
    matches = re.findall(pattern, parsed_md, re.DOTALL)
    
    for title, content in matches:
        clean_content = re.sub(r'<.*?>', '', content).strip()
        if clean_content:
            sections.append({
                "section_title": title.strip(),
                "written_content": clean_content
            })
    
    return sections

def table_of_contents(markdown_text: str) -> str:
    """
    Generate a table of contents for the given markdown text.

    Args:
        markdown_text (str): The markdown text to process.

    Returns:
        str: The generated table of contents.
    """
    def generate_table_of_contents(headers, indent_level=0):
        toc = ""
        for header in headers:
            toc += " " * (indent_level * 4) + "- " + header["text"] + "\n"
            if "children" in header:
                toc += generate_table_of_contents(header["children"], indent_level + 1)
        return toc

    try:
        headers = extract_headers(markdown_text)
        toc = "## Table of Contents\n\n" + generate_table_of_contents(headers)
        return toc
    except Exception as e:
        print("table_of_contents Exception : ", e)
        return markdown_text

def add_references(report_markdown: str, visited_urls: set) -> str:
    """
    Add references to the markdown report.

    Args:
        report_markdown (str): The existing markdown report.
        visited_urls (set): A set of URLs that have been visited during research.

    Returns:
        str: The updated markdown report with added references.
    """
    try:
        url_markdown = "\n\n\n## References\n\n"
        url_markdown += "".join(f"- [{url}]({url})\n" for url in visited_urls)
        updated_markdown_report = report_markdown + url_markdown
        return updated_markdown_report
    except Exception as e:
        print(f"Encountered exception in adding source urls : {e}")
        return report_markdown


def sanitize_citation_links(report_markdown: str, allowed_urls: set[str] | None = None) -> str:
    """
    Remove placeholder / fake citation links (e.g. example.com, '(url)') while keeping the citation text.

    This protects against LLMs emitting template placeholders like:
      ([Author, 2024](https://example.com))
      ([in-text citation](url))
    """
    try:
        import re
        from urllib.parse import urlparse

        # Match standard markdown links, but skip images: ![alt](url)
        pattern = re.compile(r"(?<!!)\[(?P<text>[^\]]+)\]\((?P<url>[^)]+)\)")

        def _is_placeholder(u: str) -> bool:
            u = (u or "").strip().strip('"').strip("'")
            if not u:
                return True
            if u.lower() == "url":
                return True
            if "example.com" in u.lower():
                return True
            return False

        def _normalize_url(u: str) -> str:
            u = (u or "").strip().strip('"').strip("'")
            return u

        def repl(m: re.Match) -> str:
            text = m.group("text")
            url = m.group("url")
            url_clean = _normalize_url(url)

            # Fast path for obvious placeholders
            if _is_placeholder(url_clean):
                return text

            # If the model kept the placeholder label, replace it with a neutral label.
            if isinstance(text, str) and text.strip().lower() == "in-text citation":
                text = "Source"

            # If we have an allow-list of sources, drop any citation link not in the allow-list.
            # This prevents hallucinated domains from polluting the report.
            if allowed_urls is not None:
                if url_clean not in allowed_urls:
                    return text

            # Some models emit malformed "url" tokens; treat non-URLs as placeholders in citations
            try:
                parsed = urlparse(url_clean)
                if parsed.scheme and parsed.netloc:
                    return m.group(0)
            except Exception:
                pass

            # If it doesn't look like a URL, drop the link but keep the label
            return text

        return pattern.sub(repl, report_markdown)
    except Exception:
        return report_markdown


def canonicalize_intext_citations(report_markdown: str, allowed_urls: set[str] | None = None) -> str:
    """
    Force in-text citations to the canonical form: ([Source](url))

    Only transforms citations that are already in a parenthetical markdown-link form:
      ([Anything](url))
    Leaves reference lists and other links untouched.
    """
    try:
        import re

        # Parenthetical markdown link: ([label](url))
        pattern = re.compile(r"\(\s*\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)\s*\)")

        def repl(m: re.Match) -> str:
            url = (m.group("url") or "").strip().strip('"').strip("'")
            if not url:
                return "(Source)"
            if allowed_urls is not None and url not in allowed_urls:
                # If it's not an allowed source, drop the link but keep neutral label
                return "(Source)"
            return f"([Source]({url}))"

        return pattern.sub(repl, report_markdown)
    except Exception:
        return report_markdown


def prune_unsupported_citation_claims(report_markdown: str) -> str:
    """
    Prune common hallucinated "study/meta-analysis found X%" style claims when they are not cited.

    This is intentionally conservative: it only drops sentences that look like
    research-claim statements AND contain no markdown links (i.e. no citations).

    Use this as a safety net; the primary defense should be prompt constraints + good context.
    """
    try:
        import re

        # Heuristics: sentences that are likely to be fabricated without sources
        risky = re.compile(
            r"\b("
            r"study|studies|meta-analysis|systematic review|randomi[sz]ed|longitudinal|cohort|trial|"
            r"found that|revealed that|demonstrated that|showed that|reported a|were \d+(\.\d+)?x|"
            r"\d+(\.\d+)?%|times more likely|statistically significant"
            r")\b",
            re.IGNORECASE,
        )

        # Split by paragraph to keep markdown structure
        paragraphs = report_markdown.split("\n\n")
        out_paras: list[str] = []
        for p in paragraphs:
            stripped = p.strip()
            if not stripped:
                out_paras.append(p)
                continue

            # Keep headers, lists, code blocks as-is
            if stripped.startswith("#") or stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("```"):
                out_paras.append(p)
                continue

            # Sentence-ish split (simple, language-agnostic enough for our use case)
            parts = re.split(r"(?<=[.!?])\s+", p)
            kept: list[str] = []
            for s in parts:
                s_strip = s.strip()
                if not s_strip:
                    continue
                has_citation_link = "](" in s_strip  # markdown link
                if (not has_citation_link) and risky.search(s_strip):
                    # Drop uncited risky claim
                    continue
                kept.append(s)

            out_paras.append(" ".join(kept).strip())

        return "\n\n".join([p for p in out_paras if p is not None])
    except Exception:
        return report_markdown