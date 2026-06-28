"""Pexels image search provider for GPT Researcher.

This module provides photo search capabilities using the Pexels API.
Images are searched, downloaded to local storage, and returned with
attribution metadata to comply with Pexels' API terms.

Pexels API Rules (from https://www.pexels.com/api/documentation/):
- Auth: Header-based (Authorization: YOUR_API_KEY)
- Rate limit: 200 requests/hour, 20,000 requests/month (default)
- Must display a prominent link to Pexels
- Should credit photographers when possible
"""

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PEXELS_API_BASE = "https://api.pexels.com/v1"


class PexelsImageSearchProvider:
    """Provider for searching and downloading images from Pexels.

    Attributes:
        api_key: Pexels API key for authentication.
        output_dir: Directory to save downloaded images.
        show_attribution: Whether to include attribution metadata.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "outputs",
        show_attribution: bool = True,
    ):
        """Initialize the PexelsImageSearchProvider.

        Args:
            api_key: Pexels API key. If not provided, reads from PEXELS_API_KEY env var.
            output_dir: Base directory for outputs (images will be in output_dir/images/pexels/).
            show_attribution: Whether to include attribution metadata.
        """
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.output_dir = Path(output_dir)
        self.show_attribution = show_attribution

        if not self.api_key:
            logger.warning(
                "No Pexels API key found. Set PEXELS_API_KEY "
                "environment variable to enable Pexels image search."
            )

    def _ensure_output_dir(self, research_id: str = "") -> Path:
        """Ensure the output directory exists and return the path."""
        if research_id:
            output_path = self.output_dir / "images" / "pexels" / research_id
        else:
            output_path = self.output_dir / "images" / "pexels"
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def _generate_filename(self, search_query: str, image_id: int, ext: str = "jpg") -> str:
        """Generate a unique filename for the downloaded image."""
        query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
        return f"pexels_{image_id}_{query_hash}.{ext}"

    def is_available(self) -> bool:
        """Check if Pexels search is available (API key is configured)."""
        return bool(self.api_key)

    async def search_photos(
        self,
        query: str,
        per_page: int = 10,
        page: int = 1,
        orientation: str = "landscape",
        size: str = "large",
    ) -> List[Dict[str, Any]]:
        """Search for photos on Pexels.

        Args:
            query: Search query string.
            per_page: Number of results per page (max 80).
            page: Page number for pagination.
            orientation: Photo orientation — landscape, portrait, or square.
            size: Photo size — large (24MP), medium (12MP), small (4MP).

        Returns:
            List of photo result dictionaries from Pexels API.
        """
        if not self.api_key:
            logger.warning("No Pexels API key configured; skipping search")
            return []

        url = f"{PEXELS_API_BASE}/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": min(per_page, 80),
            "page": page,
            "orientation": orientation,
            "size": size,
        }

        logger.info(f"Searching Pexels for: {query[:60]}...")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:
                        logger.warning("Pexels API rate limit exceeded (200 req/hour)")
                        return []
                    resp.raise_for_status()
                    data = await resp.json()
        except ImportError:
            import requests

            response = await asyncio.to_thread(
                requests.get, url, headers=headers, params=params, timeout=30
            )
            if response.status_code == 429:
                logger.warning("Pexels API rate limit exceeded (200 req/hour)")
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Pexels search failed: {e}", exc_info=True)
            return []

        photos = data.get("photos", [])
        total_results = data.get("total_results", 0)
        logger.info(f"Pexels returned {len(photos)} photos (total: {total_results})")

        return photos

    async def download_image(
        self,
        image_url: str,
        output_path: Path,
    ) -> bool:
        """Download an image from Pexels to local storage.

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

        logger.info(f"Downloaded Pexels image to: {output_path}")
        return True

    async def fetch_images(
        self,
        search_queries: List[str],
        research_id: str = "",
        max_images: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search Pexels for multiple queries and download the best result for each.

        Args:
            search_queries: List of search query strings.
            research_id: Optional research ID for file organization.
            max_images: Maximum number of images to download.

        Returns:
            List of downloaded image metadata dicts.
        """
        if not self.is_available():
            logger.info("Pexels search is not available (missing API key)")
            return []

        output_path = self._ensure_output_dir(research_id)
        downloaded_images = []

        # Limit to max_images unique queries
        unique_queries = list(dict.fromkeys(search_queries))[:max_images]

        for query in unique_queries:
            try:
                photos = await self.search_photos(query, per_page=5)
                if not photos:
                    continue

                # Pick the best hit (first result)
                best_photo = photos[0]

                # Use the 'large' size (650x940 compressed) for good quality;
                # fallback to 'medium' then 'original'
                src = best_photo.get("src", {})
                image_url = src.get("large") or src.get("medium") or src.get("original")
                if not image_url:
                    logger.warning(f"No downloadable URL found for Pexels photo: {best_photo.get('id')}")
                    continue

                # Determine file extension from URL
                ext = Path(image_url.split("?")[0]).suffix.lstrip(".") or "jpg"

                filename = self._generate_filename(query, best_photo.get("id", 0), ext)
                filepath = output_path / filename

                # Download the image
                success = await self.download_image(image_url, filepath)
                if not success:
                    continue

                # Build attribution string
                photographer = best_photo.get("photographer", "Unknown")
                photo_url = best_photo.get("url", "")
                attribution = f"Photo by {photographer} on Pexels" if self.show_attribution else ""

                # Use Pexels-provided alt text if available
                alt_text = best_photo.get("alt", f"Photo: {query}")

                # Construct both absolute path (for PDF) and web URL (for frontend)
                absolute_path = filepath.resolve()
                web_url = (
                    f"/outputs/images/pexels/{research_id}/{filename}"
                    if research_id
                    else f"/outputs/images/pexels/{filename}"
                )

                image_info = {
                    "path": str(absolute_path),
                    "url": web_url,
                    "absolute_url": str(absolute_path),
                    "prompt": query,
                    "alt_text": alt_text[:120],
                    "attribution": attribution,
                    "page_url": photo_url,
                    "photographer_url": best_photo.get("photographer_url", ""),
                    "source": "pexels",
                    "pexels_id": best_photo.get("id"),
                    "width": best_photo.get("width"),
                    "height": best_photo.get("height"),
                }

                downloaded_images.append(image_info)
                logger.info(f"Pexels image ready: {alt_text[:50]}... (by {photographer})")

            except Exception as e:
                logger.error(f"Failed to fetch Pexels image for query '{query[:50]}': {e}")
                continue

        return downloaded_images

    @classmethod
    def from_config(cls, config) -> Optional["PexelsImageSearchProvider"]:
        """Create a PexelsImageSearchProvider from a Config object."""
        enabled = getattr(config, "pexels_image_search_enabled", False)
        if not enabled:
            return None

        return cls(
            api_key=getattr(config, "pexels_api_key", None),
            show_attribution=getattr(config, "pexels_show_attribution", True),
        )
