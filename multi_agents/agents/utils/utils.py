from __future__ import annotations

import re


def sanitize_filename(filename: str) -> str:
    """Sanitize a given filename by replacing characters that are invalid

    in Windows file paths with an underscore ('_').

    This function ensures that the filename is compatible with all
    operating systems by removing or replacing characters that are
    not allowed in Windows file paths. Specifically, it replaces
    the following characters: < > : " / \\ | ? *

    Args:
        filename (str): The original filename to be sanitized.

    Returns:
        str: The sanitized filename with invalid characters replaced by an underscore.

    Examples:
    >>> sanitize_filename('invalid:file/name*example?.txt')
    'invalid_file_name_example_.txt'

    >>> sanitize_filename('valid_filename.txt')
    'valid_filename.txt'
    """
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def generate_slug(text: str, existing_slugs: set[str]) -> str:
    """Generate a URL-friendly "slug" from a string.
    It lowercases, removes special characters, replaces spaces with hyphens,
    and ensures uniqueness by appending a counter if necessary.
    """
    # Convert to lowercase
    slug: str = text.lower()
    # Remove unwanted characters (anything not a letter, number, space, or hyphen)
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Replace spaces and multiple hyphens with a single hyphen
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    if not slug:
        slug = "section"  # Default slug if text results in empty

    # Ensure uniqueness
    original_slug: str = slug
    counter: int = 1
    while slug in existing_slugs:
        slug = f"{original_slug}-{counter}"
        counter += 1
    existing_slugs.add(slug)
    return slug
