from __future__ import annotations

import hashlib
import re

from typing import TYPE_CHECKING, Any, cast
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import Tag

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    from urllib.parse import ParseResult

    from bs4 import BeautifulSoup


def get_relevant_images(
    soup: BeautifulSoup,
    url: str,
) -> list[dict[str, Any]]:
    """Extract relevant images from the page."""
    image_urls: list[dict[str, Any]] = []

    try:
        # Find all img tags with src attribute
        all_images: list[Any] = soup.find_all("img", src=True)

        for img in all_images:
            img: Tag = cast(Tag, img)
            src: str | list[str] = img.get("src", "")
            img_src: str = urljoin(url, src if isinstance(src, str) else "\n".join(src))
            if img_src.startswith(("http://", "https://")):
                score = 0
                # Check for relevant classes
                if any(
                    str(cls).casefold().strip() in img.get("class", [])
                    for cls in [
                        "header",
                        "featured",
                        "hero",
                        "thumbnail",
                        "main",
                        "content",
                    ]
                ):
                    score = 4  # Higher score
                # Check for size attributes
                elif img.get("width") and img.get("height"):
                    width: int | None = parse_dimension(img.get("width", ""))
                    height: int | None = parse_dimension(img.get("height", ""))
                    if width and height:
                        if width >= 2000 and height >= 1000:
                            score = 3  # Medium score (very large images)
                        elif width >= 1600 or height >= 800:
                            score = 2  # Low score
                        elif width >= 800 or height >= 500:
                            score = 1  # Lower score
                        elif width >= 500 or height >= 300:
                            score = 0  # Lowest score
                        # Added condition to skip images below a certain size, keeping original logic
                        else:
                            continue  # Skip small images

                image_urls.append({"url": img_src, "score": score})

    except Exception as e:
        get_formatted_logger(__name__).exception(f"Error in get_relevant_images: {e.__class__.__name__}: {e}")
        return []
    else:
        # Sort images by score (highest first)
        sorted_images: list[dict[str, Any]] = sorted(image_urls, key=lambda x: x["score"], reverse=True)

        # Select all images with score 3 and 2, then add score 1 images up to a total of 10
        high_score_images: list[dict[str, Any]] = [img for img in sorted_images if img["score"] in [3, 2]]
        low_score_images: list[dict[str, Any]] = [img for img in sorted_images if img["score"] == 1]

        result: list[dict[str, Any]] = high_score_images + low_score_images[: max(0, 10 - len(high_score_images))]
        return result[:10]  # Ensure we don't return more than 10 images in total


def parse_dimension(value: str | list[str]) -> int | None:
    """Parse dimension value, handling px units, percentages, and relative units.

    Args:
        value: A string representing the dimension value

    Returns:
        The parsed dimension value in pixels (or None if parsing failed)
    """

    # Remove whitespace
    if isinstance(value, list):
        value = "\n".join(value)
    value = value.strip().casefold()

    if value == "auto":
        return None

    # Handle percentage values
    if value.endswith("%"):
        # Calculate pixel value relative to parent size (assuming 1000px for simplicity)
        # Replace this calculation with your actual parent size if needed
        parent_size = 1000
        try:
            return int(float(value[:-1]) / 100 * parent_size)
        except ValueError:
            get_formatted_logger(__name__).warning(f"Error parsing percentage dimension value {value}")
            return None

    # Handle relative units (simplified example)
    relative_unit_pattern: re.Pattern[str] = re.compile(r"(\d+(\.\d+)?)\s*(em|vw|vh)")
    match: re.Match[str] | None = relative_unit_pattern.match(value)
    if match:
        # Resolve relative unit to pixel value (simplified example)
        # Replace this calculation with your actual logic if needed
        try:
            pixel_value: float = float(match.group(1)) * (16 if match.group(3) == "em" else 10)
        except ValueError:
            get_formatted_logger(__name__).warning(f"Error parsing relative unit dimension value {value}")
            return None
        else:
            return int(pixel_value)

    # Handle simple numeric values
    try:
        # Remove px suffix if present
        if value.endswith("px"):
            value = value[:-2]
        # Convert to integer
        return int(float(value))
    except ValueError:
        # Fallback to default value if parsing failed
        get_formatted_logger(__name__).warning(f"Error parsing dimension value {value}")
        return None


def extract_title(soup: BeautifulSoup) -> str | None:
    """Extract the title from the BeautifulSoup object."""
    return None if soup.title is None else str(soup.title.string).strip()


def get_image_hash(image_url: str) -> str | None:
    """Calculate a simple hash based on the image filename and essential query parameters."""
    try:
        parsed_url: ParseResult = urlparse(image_url)

        # Extract the filename
        filename: str = parsed_url.path.split("/")[-1]

        # Extract essential query parameters (e.g., 'url' for CDN-served images)
        query_params: dict[str, list[str]] = parse_qs(parsed_url.query)
        essential_params: list[str] = query_params.get("url", [])

        # Combine filename and essential parameters
        image_identifier: str = filename + "".join(essential_params)

        # Calculate hash
        return hashlib.md5(image_identifier.encode()).hexdigest()
    except Exception as e:
        get_formatted_logger(__name__).error(f"Error calculating image hash for {image_url}: {e}")
        return None


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Clean the soup by removing unwanted tags."""
    for tag in soup.find_all(
        [
            "footer",
            "header",
            "menu",
            "nav",
            "script",
            "sidebar",
            "style",
            "svg",
        ]
    ):
        tag.decompose()

    disallowed_class_set: set[str] = {"nav", "menu", "sidebar", "footer"}

    # clean tags with certain classes
    from bs4 import Tag

    def does_tag_have_disallowed_class(elem: Any) -> bool:
        if not isinstance(elem, Tag):  # Corrected type check
            return False

        return any(cls_name in disallowed_class_set for cls_name in elem.get("class", []))

    for tag in soup.find_all(does_tag_have_disallowed_class):
        if not isinstance(tag, Tag):
            continue
        tag.decompose()

    return soup


def get_text_from_soup(soup: BeautifulSoup) -> str:
    """Get the relevant text from the soup with improved filtering."""
    text = soup.get_text(strip=True, separator="\n")
    # Remove excess whitespace
    text = re.sub(r"\s{2,}", " ", text)
    return text
