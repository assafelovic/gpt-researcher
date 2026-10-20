"""Utility functions for web scraping.

This module provides helper functions for extracting content, images,
and processing HTML from web pages.
"""

import hashlib
import logging
import re
from urllib.parse import parse_qs, urljoin, urlparse

import bs4
from bs4 import BeautifulSoup


def get_relevant_images(soup: BeautifulSoup, url: str) -> list:
    """Extract relevant images from the page"""
    image_urls = []
    
    try:
        if soup is None:
            return []
        # Find all img tags with src attribute
        all_images = soup.find_all('img', src=True)
        
        for img in all_images:
            img_src = urljoin(url, img['src'])
            if img_src.startswith(('http://', 'https://')):
                score = 0
                # Check for relevant classes
                classes = img.get("class") or []
                if isinstance(classes, str):
                    classes = classes.split()
                elif not isinstance(classes, (list, tuple, set)):
                    classes = []
                if any(cls in classes for cls in ['header', 'featured', 'hero', 'thumbnail', 'main', 'content']):
                    score = 4  # Higher score
                # Check for size attributes
                elif img.get('width') and img.get('height'):
                    width = parse_dimension(img['width'])
                    height = parse_dimension(img['height'])
                    if width and height:
                        if width >= 2000 and height >= 1000:
                            score = 3  # Medium score (very large images)
                        elif width >= 1600 or height >= 800:
                            score = 2  # Lower score
                        elif width >= 800 or height >= 500:
                            score = 1  # Lowest score
                        elif width >= 500 or height >= 300:
                            score = 0  # Lowest score
                        else:
                            continue  # Skip small images
                
                image_urls.append({'url': img_src, 'score': score})
        
        # Sort images by score (highest first)
        sorted_images = sorted(image_urls, key=lambda x: x['score'], reverse=True)
        
        return sorted_images[:10]  # Ensure we don't return more than 10 images in total
    
    except Exception as e:
        logging.error(f"Error in get_relevant_images: {e}")
        return []

def parse_dimension(value: str) -> int:
    """Parse dimension value, handling px units"""
    # HTML width/height attrs are often missing or non-string; callers pass
    # img.get('width') which may be None.
    if value is None:
        return None
    if not isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError) as e:
            logging.debug("Could not parse dimension value %r: %s", value, e)
            return None
    if value.lower().endswith('px'):
        value = value[:-2]  # Remove 'px' suffix
    try:
        # Convert to float first to handle decimal values like '409.12'
        return int(float(value))
    except (ValueError, TypeError) as e:
        # Non-numeric dimensions (e.g. '100%', 'auto', '50em') are common and
        # expected on real pages; log at debug level instead of spamming stdout.
        logging.debug("Could not parse dimension value %r: %s", value, e)
        return None

def extract_title(soup: BeautifulSoup) -> str:
    """Extract the title text from the BeautifulSoup object.

    Always returns a string. An empty ``<title></title>`` yields ``""`` (not
    ``None``), and a title containing nested markup (e.g.
    ``<title><span>x</span></title>``) yields its text content rather than the
    raw inner HTML.
    """
    title_tag = soup.title
    if not title_tag:
        return ""
    return title_tag.get_text(strip=True)

def get_image_hash(image_url: str) -> str:
    """Calculate a simple hash based on the image filename and essential query parameters"""
    try:
        parsed_url = urlparse(image_url)
        
        # Extract the filename
        filename = parsed_url.path.split('/')[-1]
        
        # Extract essential query parameters (e.g., 'url' for CDN-served images)
        query_params = parse_qs(parsed_url.query)
        essential_params = query_params.get('url', [])
        
        # Combine filename and essential parameters
        image_identifier = filename + ''.join(essential_params)
        
        # Calculate hash
        return hashlib.md5(image_identifier.encode()).hexdigest()
    except Exception as e:
        logging.error(f"Error calculating image hash for {image_url}: {e}")
        return None


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Clean the soup by removing unwanted tags"""
    for tag in soup.find_all(
        [
            "script",
            "style",
            "footer",
            "header",
            "nav",
            "menu",
            "sidebar",
            "svg",
        ]
    ):
        tag.decompose()

    disallowed_class_set = {"nav", "menu", "sidebar", "footer"}

    # clean tags with certain classes
    def does_tag_have_disallowed_class(elem) -> bool:
        if not isinstance(elem, bs4.Tag):
            return False

        return any(
            cls_name in disallowed_class_set for cls_name in elem.get("class", [])
        )

    for tag in soup.find_all(does_tag_have_disallowed_class):
        tag.decompose()

    return soup


# Elements a browser lays out as blocks. Each one starts a new line of extracted
# text, while the text of any other element stays in the line around it.
_BLOCK_TAGS = frozenset(
    "address article aside blockquote body caption center dd details dialog dir div dl dt"
    " fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html"
    " legend li listing main menu nav ol optgroup option p plaintext pre search section"
    " summary table tbody td textarea tfoot th thead title tr ul xmp".split()
)
# Whitespace inside these elements is content, so their text is kept as written.
_PREFORMATTED_TAGS = frozenset(("listing", "plaintext", "pre", "textarea", "xmp"))
# Inline boxes whose text never runs into the text next to them.
_BOX_TAGS = frozenset(("button", "select"))
# Only these characters are whitespace in HTML. A no-break space is content.
_HTML_WHITESPACE = re.compile(r"[ \t\n\r\f]+")


def _block_lines(soup: BeautifulSoup) -> list[str]:
    """Return the text of the soup as one line per block element.

    ``soup.get_text(separator="\\n")`` puts every text node on its own line, so
    a link or an emphasis split the sentence, and even the word, it sat in.
    """
    lines: list[str] = []
    line: list[str] = []

    def end_line() -> None:
        text = _HTML_WHITESPACE.sub(" ", "".join(line)).strip(" ")
        line.clear()
        if text.strip():
            lines.append(text)

    # An explicit stack, so deeply nested markup cannot exhaust the recursion limit.
    stack: list[tuple[bs4.PageElement, str]] = [(soup, "visit")]
    while stack:
        node, action = stack.pop()
        if action == "end_line":
            end_line()
        elif action == "space":
            line.append(" ")
        elif isinstance(node, bs4.Tag):
            if node.name == "br":
                end_line()
            elif node.name in _PREFORMATTED_TAGS:
                end_line()
                text = node.get_text().strip("\n")
                if text.strip():
                    lines.append(text)
            else:
                if node.name in _BLOCK_TAGS:
                    end_line()
                    stack.append((node, "end_line"))
                elif node.name in _BOX_TAGS:
                    line.append(" ")
                    stack.append((node, "space"))
                stack.extend((child, "visit") for child in reversed(node.contents))
        # Script, style, template and comment strings are subclasses and are
        # not page text, the same filter get_text() applies by default.
        elif type(node) in (bs4.NavigableString, bs4.CData):
            line.append(str(node))
    end_line()
    return lines


def get_text_from_soup(soup: BeautifulSoup) -> str:
    """Get the relevant text from the soup with improved filtering"""
    if soup is None:
        return ""
    text = "\n".join(_block_lines(soup))
    # Remove excess whitespace
    text = re.sub(r"\s{2,}", " ", text)
    return text
