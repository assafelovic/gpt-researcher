from __future__ import annotations

import hashlib
import logging
import re

from typing import Any
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

import bs4

from bs4 import BeautifulSoup


def get_relevant_images(
    soup: BeautifulSoup,
    url: str,
) -> list[dict[str, Any]]:
    """Extract relevant images from the page"""
    image_urls: list[dict[str, Any]] = []

    try:
        # Find all img tags with src attribute
        all_images: list[bs4.element.Tag] = soup.find_all("img", src=True)

        for img in all_images:
            img_src: str = urljoin(url, img["src"])  # pyright: ignore[reportIndexIssue]
            if img_src.startswith(("http://", "https://")):
                score = 0
                # Check for relevant classes
                if any(cls in img.get("class", []) for cls in ["header", "featured", "hero", "thumbnail", "main", "content"]):  # pyright: ignore[reportOperatorIssue, reportAttributeAccessIssue]
                    score = 4  # Higher score
                # Check for size attributes
                elif img.get("width") and img.get("height"):  # pyright: ignore[reportAttributeAccessIssue]
                    width: int = parse_dimension(img["width"])  # pyright: ignore[reportIndexIssue]
                    height: int = parse_dimension(img["height"])  # pyright: ignore[reportIndexIssue]
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

                image_urls.append({"url": img_src, "score": score})

        # Sort images by score (highest first)
        sorted_images: list[dict[str, Any]] = sorted(image_urls, key=lambda x: x["score"], reverse=True)

        # Select all images with score 3 and 2, then add score 1 images up to a total of 10
        high_score_images: list[dict[str, Any]] = [img for img in sorted_images if img["score"] in [3, 2]]
        low_score_images: list[dict[str, Any]] = [img for img in sorted_images if img["score"] == 1]

        result: list[dict[str, Any]] = high_score_images + low_score_images[: max(0, 10 - len(high_score_images))]
        return result[:10]  # Ensure we don't return more than 10 images in total

    except Exception as e:
        logging.error(f"Error in get_relevant_images: {e.__class__.__name__}: {e}")
        return []


def parse_dimension(value: str) -> int | None:
    """Parse dimension value, handling px units"""
    if value.lower().endswith("px"):
        value = value[:-2]  # Remove 'px' suffix
    try:
        return int(float(value))  # Convert to float first to handle decimal values
    except ValueError as e:
        print(f"Error parsing dimension value {value}: {e.__class__.__name__}: {e}")
        return None


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the title from the BeautifulSoup object"""
    return str(soup.title.string) if soup.title else ""


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
        logging.error(f"Error calculating image hash for {image_url}: {e.__class__.__name__}: {e}")
        return None


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Clean the soup by removing unwanted tags."""
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

    disallowed_class_set: set[str] = {"nav", "menu", "sidebar", "footer"}

    # clean tags with certain classes
    def does_tag_have_disallowed_class(elem: bs4.Tag | Any) -> bool:
        if not isinstance(elem, bs4.Tag):
            return False

        return any(cls_name in disallowed_class_set for cls_name in elem.get("class", []) or [])

    for tag in soup.find_all(does_tag_have_disallowed_class):
        tag.decompose()

    return soup


def get_text_from_soup(soup: BeautifulSoup) -> str:
    """Get the relevant text from the soup with improved filtering"""
    text: str = soup.get_text(strip=True, separator="\n")
    # Remove excess whitespace
    text = re.sub(r"\s{2,}", " ", text)
    return text
