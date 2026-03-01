"""ModelsLab image generation provider for GPT Researcher.

This module provides image generation via ModelsLab's API, supporting
Flux, SDXL, Stable Diffusion, and 50k+ community models.

API docs: https://docs.modelslab.com
"""

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TEXT2IMG_URL = "https://modelslab.com/api/v6/images/text2img"
FETCH_BASE_URL = "https://modelslab.com/api/v6/images/fetch"
MAX_POLL_ATTEMPTS = 12
POLL_INTERVAL_SECONDS = 5


class ModelsLabImageGeneratorProvider:
    """Provider for generating images using ModelsLab's API.

    Supports Flux, SDXL, Stable Diffusion, and thousands of community
    models. Auth uses API key in the request body (not Bearer token).

    Attributes:
        model_id: The ModelsLab model to use (default: "flux").
        api_key: ModelsLab API key from modelslab.com/account/api-key.
        output_dir: Directory to save generated images.
    """

    DEFAULT_MODEL = "flux"

    def __init__(
        self,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        output_dir: str = "outputs",
    ):
        self.model_id = model_id or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv("MODELSLAB_API_KEY")
        self.output_dir = Path(output_dir)

        if not self.api_key:
            logger.warning(
                "No ModelsLab API key found. Set MODELSLAB_API_KEY "
                "environment variable to enable image generation."
            )

    def _ensure_output_dir(self, research_id: str = "") -> Path:
        path = (
            self.output_dir / "images" / research_id
            if research_id
            else self.output_dir / "images"
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _generate_filename(self, prompt: str, index: int = 0) -> str:
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"img_{prompt_hash}_{index}.png"

    async def _download_image(self, url: str) -> bytes:
        """Download image from URL asynchronously."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    resp.raise_for_status()
                    return await resp.read()
        except ImportError:
            # Fallback to requests in thread if aiohttp not available
            import requests

            response = await asyncio.to_thread(requests.get, url, timeout=30)
            response.raise_for_status()
            return response.content

    async def _poll_for_result(self, request_id: str) -> List[str]:
        """Poll the fetch endpoint until generation completes."""
        try:
            import aiohttp

            for _ in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{FETCH_BASE_URL}/{request_id}",
                        json={"key": self.api_key},
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        body = await resp.json()
                        if body.get("status") == "success" and body.get("output"):
                            return body["output"]
                        if body.get("status") == "error":
                            raise RuntimeError(
                                body.get("messege", "ModelsLab generation error")
                            )
        except ImportError:
            import requests

            for _ in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                resp = await asyncio.to_thread(
                    requests.post,
                    f"{FETCH_BASE_URL}/{request_id}",
                    json={"key": self.api_key},
                    timeout=15,
                )
                body = resp.json()
                if body.get("status") == "success" and body.get("output"):
                    return body["output"]
                if body.get("status") == "error":
                    raise RuntimeError(body.get("messege", "ModelsLab generation error"))

        raise TimeoutError("ModelsLab image generation timed out after polling.")

    async def generate_image(
        self,
        prompt: str,
        context: str = "",
        research_id: str = "",
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        style: str = "dark",
    ) -> List[Dict[str, Any]]:
        """Generate images using ModelsLab's text-to-image API.

        Args:
            prompt: The image generation prompt.
            context: Additional context (appended to prompt).
            research_id: Research ID for organizing output directories.
            aspect_ratio: Ignored (ModelsLab uses width/height).
            num_images: Number of images to generate (1–4).
            style: Ignored (prompt controls style directly).

        Returns:
            List of dicts with path, url, prompt, and alt_text keys.
        """
        if not self.api_key:
            logger.warning("No ModelsLab API key set; skipping image generation.")
            return []

        output_path = self._ensure_output_dir(research_id)
        full_prompt = f"{prompt}. {context}" if context else prompt
        samples = min(max(1, num_images), 4)

        payload = {
            "key": self.api_key,
            "model_id": self.model_id,
            "prompt": full_prompt,
            "negative_prompt": "low quality, blurry, watermark, text, nsfw",
            "width": 768,
            "height": 512,
            "samples": samples,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "seed": -1,
            "safety_checker": "yes",
        }

        try:
            image_urls = await self._request_images(payload)
        except Exception as exc:
            logger.error(f"ModelsLab image generation failed: {exc}", exc_info=True)
            return []

        results = []
        for i, url in enumerate(image_urls[:num_images]):
            try:
                image_bytes = await self._download_image(url)
                filename = self._generate_filename(prompt, i)
                filepath = output_path / filename
                with open(filepath, "wb") as fh:
                    fh.write(image_bytes)

                absolute_path = filepath.resolve()
                web_url = (
                    f"/outputs/images/{research_id}/{filename}"
                    if research_id
                    else f"/outputs/images/{filename}"
                )
                results.append(
                    {
                        "path": str(absolute_path),
                        "url": web_url,
                        "absolute_url": str(absolute_path),
                        "prompt": prompt,
                        "alt_text": f"Illustration: {prompt[:120]}",
                    }
                )
                logger.info(f"ModelsLab image saved to: {filepath}")
            except Exception as exc:
                logger.error(f"Failed to download image {i}: {exc}")

        return results

    async def _request_images(self, payload: Dict[str, Any]) -> List[str]:
        """POST to text2img endpoint and handle async processing."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    TEXT2IMG_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    body = await resp.json()
        except ImportError:
            import requests

            body = await asyncio.to_thread(
                lambda: requests.post(TEXT2IMG_URL, json=payload, timeout=30).json()
            )

        if body.get("status") == "error":
            raise RuntimeError(body.get("messege", "ModelsLab API error"))

        if body.get("status") == "processing" and body.get("id"):
            return await self._poll_for_result(body["id"])

        return body.get("output", [])

    def is_available(self) -> bool:
        """Return True if the API key is configured."""
        return bool(self.api_key)

    @classmethod
    def from_config(cls, config) -> Optional["ModelsLabImageGeneratorProvider"]:
        """Create a ModelsLabImageGeneratorProvider from a Config object."""
        enabled = getattr(config, "IMAGE_GENERATION_ENABLED", False)
        provider = getattr(config, "IMAGE_GENERATION_PROVIDER", "google")
        if not enabled or provider != "modelslab":
            return None
        model = getattr(config, "IMAGE_GENERATION_MODEL", None)
        return cls(model_id=model or cls.DEFAULT_MODEL)
