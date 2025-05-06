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