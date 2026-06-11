"""Unsplash image search provider for GPT Researcher.

This module provides photo search capabilities using the Unsplash API.
Unlike Pixabay and Pexels, Unsplash REQUIRES hotlinking — images must be
served directly from Unsplash's CDN to enable accurate view tracking for
photographers. Do NOT download or re-host Unsplash images.

Unsplash API Rules (from https://unsplash.com/documentation):
- Auth: Header-based (Authorization: Client-ID YOUR_ACCESS_KEY)
- Rate limit: 50 requests/hour (demo), 1,000 requests/hour (production)
- Hotlinking REQUIRED — embed URLs directly, do not download/re-host
- Must preserve the `ixid` parameter on all image URLs
- Must attribute photographer and Unsplash
- content_filter: low (default) or high
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

UNSPLASH_API_BASE = "https://api.unsplash.com"


class UnsplashImageSearchProvider:
    """Provider for searching images from Unsplash.

    Unlike other providers, this does NOT download images locally.
    Unsplash requires hotlinking via their CDN for tracking purposes.

    Attributes:
        access_key: Unsplash Access Key for authentication.
        show_attribution: Whether to include attribution metadata.
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        show_attribution: bool = True,
    ):
        """Initialize the UnsplashImageSearchProvider.

        Args:
            access_key: Unsplash Access Key. If not provided, reads from UNSPLASH_ACCESS_KEY env var.
            show_attribution: Whether to include attribution metadata.
        """
        self.access_key = access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.show_attribution = show_attribution

        if not self.access_key:
            logger.warning(
                "No Unsplash Access Key found. Set UNSPLASH_ACCESS_KEY "
                "environment variable to enable Unsplash image search."
            )

    def is_available(self) -> bool:
        """Check if Unsplash search is available (access key is configured)."""
        return bool(self.access_key)

    async def search_photos(
        self,
        query: str,
        per_page: int = 10,
        page: int = 1,
        orientation: str = "landscape",
        content_filter: str = "low",
    ) -> List[Dict[str, Any]]:
        """Search for photos on Unsplash.

        Args:
            query: Search query string.
            per_page: Number of results per page (max 30).
            page: Page number for pagination.
            orientation: Photo orientation — landscape, portrait, or squarish.
            content_filter: Content safety — low (default) or high.

        Returns:
            List of photo result dictionaries from Unsplash API.
        """
        if not self.access_key:
            logger.warning("No Unsplash Access Key configured; skipping search")
            return []

        url = f"{UNSPLASH_API_BASE}/search/photos"
        headers = {
            "Authorization": f"Client-ID {self.access_key}",
            "Accept-Version": "v1",
        }
        params = {
            "query": query,
            "per_page": min(per_page, 30),
            "page": page,
            "orientation": orientation,
            "content_filter": content_filter,
        }

        logger.info(f"Searching Unsplash for: {query[:60]}...")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 403:
                        logger.warning("Unsplash API rate limit exceeded (50 req/hour demo)")
                        return []
                    resp.raise_for_status()
                    data = await resp.json()
        except ImportError:
            import requests

            response = await asyncio.to_thread(
                requests.get, url, headers=headers, params=params, timeout=30
            )
            if response.status_code == 403:
                logger.warning("Unsplash API rate limit exceeded (50 req/hour demo)")
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Unsplash search failed: {e}", exc_info=True)
            return []

        results = data.get("results", [])
        total = data.get("total", 0)
        logger.info(f"Unsplash returned {len(results)} photos (total: {total})")

        return results

    async def fetch_images(
        self,
        search_queries: List[str],
        max_images: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search Unsplash for multiple queries and return the best result for each.

        Unsplash requires hotlinking — images are NOT downloaded locally.
        The returned URLs point directly to Unsplash's CDN.

        Args:
            search_queries: List of search query strings.
            max_images: Maximum number of images to return.

        Returns:
            List of image metadata dicts with Unsplash CDN URLs.
        """
        if not self.is_available():
            logger.info("Unsplash search is not available (missing access key)")
            return []

        found_images = []

        # Limit to max_images unique queries
        unique_queries = list(dict.fromkeys(search_queries))[:max_images]

        for query in unique_queries:
            try:
                results = await self.search_photos(query, per_page=5)
                if not results:
                    continue

                # Pick the best hit (first result = most relevant)
                best_photo = results[0]

                # Use 'regular' size (1080px width) as a good default
                urls = best_photo.get("urls", {})
                image_url = urls.get("regular") or urls.get("small") or urls.get("full")
                if not image_url:
                    logger.warning(f"No image URL found for Unsplash photo: {best_photo.get('id')}")
                    continue

                # Build attribution string
                user = best_photo.get("user", {})
                photographer = user.get("name", "Unknown")
                photo_links = best_photo.get("links", {})
                photo_html_url = photo_links.get("html", "")
                user_links = user.get("links", {})
                photographer_url = user_links.get("html", "")

                attribution = f"Photo by {photographer} on Unsplash" if self.show_attribution else ""

                # Use description or alt text if available
                alt_text = best_photo.get("alt_description") or best_photo.get("description") or f"Photo: {query}"

                image_info = {
                    "path": image_url,  # For Unsplash, path is the CDN URL
                    "url": image_url,
                    "absolute_url": image_url,
                    "prompt": query,
                    "alt_text": alt_text[:120],
                    "attribution": attribution,
                    "page_url": photo_html_url,
                    "photographer_url": photographer_url,
                    "source": "unsplash",
                    "unsplash_id": best_photo.get("id"),
                    "width": best_photo.get("width"),
                    "height": best_photo.get("height"),
                    "blur_hash": best_photo.get("blur_hash"),
                }

                found_images.append(image_info)
                logger.info(f"Unsplash image ready: {alt_text[:50]}... (by {photographer})")

            except Exception as e:
                logger.error(f"Failed to fetch Unsplash image for query '{query[:50]}': {e}")
                continue

        return found_images

    @classmethod
    def from_config(cls, config) -> Optional["UnsplashImageSearchProvider"]:
        """Create an UnsplashImageSearchProvider from a Config object."""
        enabled = getattr(config, "unsplash_image_search_enabled", False)
        if not enabled:
            return None

        return cls(
            access_key=getattr(config, "unsplash_access_key", None),
            show_attribution=getattr(config, "unsplash_show_attribution", True),
        )
