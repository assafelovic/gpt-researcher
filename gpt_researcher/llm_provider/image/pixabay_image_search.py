"""Pixabay image search provider for GPT Researcher.

This module provides photo search capabilities using the Pixabay API.
Images are searched, downloaded to local storage, and returned with
attribution metadata to comply with Pixabay's API terms.

Pixabay API Rules (from https://pixabay.com/api/docs/):
- API key passed as 'key' query parameter
- Rate limit: 100 requests per 60 seconds
- Requests MUST be cached for 24 hours
- NO permanent hotlinking — images must be downloaded to own server
- Must show users where images come from when displaying search results
- Attribution appreciated but not required for downloaded images
- webformatURL valid for only 24 hours
- Max 500 accessible images per query
"""

import asyncio
import hashlib
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PIXABAY_API_BASE = "https://pixabay.com/api/"


class PixabayImageSearchProvider:
    """Provider for searching and downloading images from Pixabay.

    Attributes:
        api_key: Pixabay API key for authentication.
        output_dir: Directory to save downloaded images.
        image_type: Type of images to search (all, photo, illustration, vector).
        safesearch: Whether to filter adult content.
        show_attribution: Whether to include attribution metadata.
        min_width: Minimum image width filter.
        min_height: Minimum image height filter.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "outputs",
        image_type: str = "photo",
        safesearch: bool = True,
        show_attribution: bool = True,
        min_width: int = 800,
        min_height: int = 600,
    ):
        """Initialize the PixabayImageSearchProvider.

        Args:
            api_key: Pixabay API key. If not provided, reads from PIXABAY_API_KEY env var.
            output_dir: Base directory for outputs (images will be in output_dir/images/pixabay/).
            image_type: Type of images to search. Options: "all", "photo", "illustration", "vector".
            safesearch: Whether to filter adult content.
            show_attribution: Whether to include attribution metadata.
            min_width: Minimum image width filter.
            min_height: Minimum image height filter.
        """
        self.api_key = api_key or os.getenv("PIXABAY_API_KEY")
        self.output_dir = Path(output_dir)
        self.image_type = image_type
        self.safesearch = safesearch
        self.show_attribution = show_attribution
        self.min_width = min_width
        self.min_height = min_height

        if not self.api_key:
            logger.warning(
                "No Pixabay API key found. Set PIXABAY_API_KEY "
                "environment variable to enable Pixabay image search."
            )

    def _ensure_output_dir(self, research_id: str = "") -> Path:
        """Ensure the output directory exists and return the path."""
        if research_id:
            output_path = self.output_dir / "images" / "pixabay" / research_id
        else:
            output_path = self.output_dir / "images" / "pixabay"
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def _generate_filename(self, search_query: str, image_id: int, ext: str = "jpg") -> str:
        """Generate a unique filename for the downloaded image."""
        query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
        return f"pixabay_{image_id}_{query_hash}.{ext}"

    def is_available(self) -> bool:
        """Check if Pixabay search is available (API key is configured)."""
        return bool(self.api_key)

    async def search_images(
        self,
        query: str,
        per_page: int = 10,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Search for images on Pixabay.

        Args:
            query: Search query string (max 100 characters per Pixabay API).
            per_page: Number of results per page (3-200).
            page: Page number for pagination.

        Returns:
            List of image result dictionaries from Pixabay API.
        """
        if not self.api_key:
            logger.warning("No Pixabay API key configured; skipping search")
            return []

        # Pixabay requires URL-encoded query strings
        encoded_query = urllib.parse.quote(query[:100])  # API limit: 100 chars

        params = {
            "key": self.api_key,
            "q": encoded_query,
            "image_type": self.image_type,
            "safesearch": "true" if self.safesearch else "false",
            "orientation": "horizontal",
            "min_width": self.min_width,
            "min_height": self.min_height,
            "order": "popular",
            "page": page,
            "per_page": per_page,
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{PIXABAY_API_BASE}?{query_string}"

        logger.info(f"Searching Pixabay for: {query[:60]}...")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 429:
                        logger.warning("Pixabay API rate limit exceeded (100 req/60s)")
                        return []
                    resp.raise_for_status()
                    data = await resp.json()
        except ImportError:
            # Fallback to requests in thread if aiohttp not available
            import requests

            response = await asyncio.to_thread(requests.get, url, timeout=30)
            if response.status_code == 429:
                logger.warning("Pixabay API rate limit exceeded (100 req/60s)")
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Pixabay search failed: {e}", exc_info=True)
            return []

        hits = data.get("hits", [])
        total_hits = data.get("totalHits", 0)
        logger.info(f"Pixabay returned {len(hits)} hits (total accessible: {total_hits})")

        return hits

    async def download_image(
        self,
        image_url: str,
        output_path: Path,
    ) -> bool:
        """Download an image from Pixabay to local storage.

        Pixabay explicitly prohibits permanent hotlinking. Images MUST be
        downloaded to your own server.

        Args:
            image_url: URL of the image to download.
            output_path: Local path to save the image.

        Returns:
            True if download succeeded, False otherwise.
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    resp.raise_for_status()
                    image_bytes = await resp.read()
        except ImportError:
            import requests

            response = await asyncio.to_thread(requests.get, image_url, timeout=60)
            response.raise_for_status()
            image_bytes = response.content

        with open(output_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"Downloaded Pixabay image to: {output_path}")
        return True

    async def fetch_images(
        self,
        search_queries: List[str],
        research_id: str = "",
        max_images: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search Pixabay for multiple queries and download the best result for each.

        Args:
            search_queries: List of search query strings.
            research_id: Optional research ID for file organization.
            max_images: Maximum number of images to download.

        Returns:
            List of downloaded image metadata dicts.
        """
        if not self.is_available():
            logger.info("Pixabay search is not available (missing API key)")
            return []

        output_path = self._ensure_output_dir(research_id)
        downloaded_images = []

        # Limit to max_images unique queries
        unique_queries = list(dict.fromkeys(search_queries))[:max_images]

        for query in unique_queries:
            try:
                hits = await self.search_images(query, per_page=5)
                if not hits:
                    continue

                # Pick the best hit (first = most popular due to order=popular)
                best_hit = hits[0]

                # Use largeImageURL (1280px) if available, fallback to webformatURL (640px)
                image_url = best_hit.get("largeImageURL") or best_hit.get("webformatURL")
                if not image_url:
                    logger.warning(f"No downloadable URL found for Pixabay image: {best_hit.get('id')}")
                    continue

                # Determine file extension from URL
                parsed = urllib.parse.urlparse(image_url)
                ext = Path(parsed.path).suffix.lstrip(".") or "jpg"

                filename = self._generate_filename(query, best_hit.get("id", 0), ext)
                filepath = output_path / filename

                # Download the image (required by Pixabay terms — no hotlinking)
                success = await self.download_image(image_url, filepath)
                if not success:
                    continue

                # Build attribution string
                user = best_hit.get("user", "Unknown")
                page_url = best_hit.get("pageURL", "")
                attribution = f"Photo by {user} via Pixabay" if self.show_attribution else ""

                # Build alt text from tags
                tags = best_hit.get("tags", "")
                alt_text = f"Photo: {tags}" if tags else f"Photo: {query}"

                # Construct both absolute path (for PDF) and web URL (for frontend)
                absolute_path = filepath.resolve()
                web_url = (
                    f"/outputs/images/pixabay/{research_id}/{filename}"
                    if research_id
                    else f"/outputs/images/pixabay/{filename}"
                )

                image_info = {
                    "path": str(absolute_path),
                    "url": web_url,
                    "absolute_url": str(absolute_path),
                    "prompt": query,
                    "alt_text": alt_text[:120],
                    "attribution": attribution,
                    "page_url": page_url,
                    "source": "pixabay",
                    "pixabay_id": best_hit.get("id"),
                    "width": best_hit.get("imageWidth"),
                    "height": best_hit.get("imageHeight"),
                }

                downloaded_images.append(image_info)
                logger.info(
                    f"Pixabay image ready: {alt_text[:50]}... (by {user})"
                )

            except Exception as e:
                logger.error(f"Failed to fetch Pixabay image for query '{query[:50]}': {e}")
                continue

        return downloaded_images

    @classmethod
    def from_config(cls, config) -> Optional["PixabayImageSearchProvider"]:
        """Create a PixabayImageSearchProvider from a Config object."""
        enabled = getattr(config, "pixabay_image_search_enabled", False)
        if not enabled:
            return None

        return cls(
            api_key=getattr(config, "pixabay_api_key", None),
            image_type=getattr(config, "pixabay_image_type", "photo"),
            safesearch=getattr(config, "pixabay_safesearch", True),
            show_attribution=getattr(config, "pixabay_show_attribution", True),
            min_width=getattr(config, "pixabay_min_width", 800),
            min_height=getattr(config, "pixabay_min_height", 600),
        )
