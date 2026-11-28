"""Vision analyzer skill for GPT Researcher.

This module provides the VisionAnalyzer class that adds visual evidence to
the research context. Scraped pages already yield image URLs, but until now
only the text of a page reached the report writer, so visual information
(charts, diagrams, tables embedded as images, figures with captions) was
silently dropped. The VisionAnalyzer sends the most relevant scraped images
to a vision-language model and injects a compact caption/OCR block into the
source content that is later compressed into the report context.

Design notes:
- VLM calls go through the shared LLM layer (create_chat_completion), so cost
  tracking (cost_callback), retries, LLM_TIMEOUT and every configured provider
  apply, exactly like the other LLM calls in the project. Only the image
  download is handled here.
- Everything is opt-in through VISION_ENABLED and fails open: a missing
  image, a slow endpoint, or a malformed answer is logged and skipped so the
  standard research flow keeps working.
- The model is selected with VISION_LLM=provider:model (same convention as
  FAST_LLM / SMART_LLM / STRATEGIC_LLM).
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Optional

import httpx
import json_repair

from ..actions.utils import stream_output
from ..utils.llm import create_chat_completion
from ..utils.url_security import UnsafeURLError, validate_url

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You analyze images extracted from web pages for a deep research agent. "
    "Return compact factual JSON and nothing else."
)

_USER_PROMPT_TEMPLATE = """Research query: {query}
Image source page: {title} ({url})

Analyze the image and return JSON with exactly these keys:
- "caption": one sentence describing what the image shows, factually;
- "text": any legible text in the image (OCR), or "" if none;
- "relevant": true if the image is useful evidence for the query, else false.
"""

# Cap on how much caption text is appended to a single source's raw content.
_CAPTION_BLOCK_MAX_CHARS = 1500


class VisionAnalyzer:
    """Injects VLM-written descriptions of scraped images into the research context.

    Attributes:
        researcher: The parent GPTResearcher instance.
        enabled: Whether image understanding is switched on via config.
        provider: LLM provider name from VISION_LLM (e.g. "openai").
        model: VLM model name from VISION_LLM (e.g. "gpt-5.4-mini").
    """

    def __init__(self, researcher):
        """Initialize the analyzer from the researcher config.

        No network calls happen here; the first analysis only runs when the
        research pipeline explicitly hands scraped sources over.

        Args:
            researcher: The GPTResearcher instance that owns this skill.
        """
        self.researcher = researcher
        self.cfg = researcher.cfg
        self._semaphore = asyncio.Semaphore(4)
        self._resolve_settings()

    def _resolve_settings(self) -> None:
        """Read VISION_* settings from the config (env vars already merged)."""
        cfg = self.cfg
        self.enabled = bool(getattr(cfg, "vision_enabled", False))
        # VISION_LLM is parsed by Config into provider + model, like FAST_LLM.
        self.provider = getattr(cfg, "vision_llm_provider", None)
        self.model = getattr(cfg, "vision_llm_model", None)
        self.max_images = int(getattr(cfg, "vision_max_images", 3) or 3)
        self.max_images_per_source = int(
            getattr(cfg, "vision_max_images_per_source", 2) or 2
        )
        self.max_image_bytes = int(
            getattr(cfg, "vision_max_image_bytes", 8000000) or 8000000
        )
        self.timeout = float(getattr(cfg, "vision_timeout", 60.0) or 60.0)
        self.embed_in_context = bool(
            getattr(cfg, "vision_embed_in_context", True)
        )
        if self.enabled and not (self.provider and self.model):
            logger.warning(
                "VISION_ENABLED is set but VISION_LLM is not configured; "
                "image understanding stays disabled."
            )
            self.enabled = False
        # Used in tests / integrations that stub the network layer.
        self.image_downloader = None
        self.vlm_caller = None

    def is_enabled(self) -> bool:
        """Return True when image understanding is switched on and configured.

        Returns:
            True if VISION_ENABLED is set and VISION_LLM resolves to a model.
        """
        return self.enabled

    async def analyze(self, scraped_data: list[dict], query: str) -> list[dict]:
        """Analyze the most relevant images of a list of scraped sources.

        The top images across all sources are described by the VLM, then a
        short "Visual evidence" block is appended to each source's raw
        content so it flows into the same compression pipeline as the page
        text. A structured image_captions field is also stored on each
        source for downstream consumers. Images the VLM marks as irrelevant
        are dropped and never reach the context.

        Args:
            scraped_data: List of scraped source dicts (url, title,
                raw_content, image_urls, ...).
            query: The research sub-question the images are judged against.

        Returns:
            The same list of sources, enriched in place.
        """
        if not self.is_enabled() or not scraped_data:
            return scraped_data

        candidates = self._select_images(scraped_data)
        if not candidates:
            return scraped_data

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "vision_analyzing",
                f"🖼️ Analyzing {len(candidates)} scraped image(s) with {self.model}...",
                self.researcher.websocket,
            )

        results = await asyncio.gather(
            *[
                self._analyze_image(candidate["url"], candidate["title"], query)
                for candidate in candidates
            ],
            return_exceptions=False,
        )

        by_source: dict[int, list[dict]] = {}
        for candidate, description in zip(candidates, results):
            if description and description.get("relevant", True):
                by_source.setdefault(candidate["source_index"], []).append(description)

        for source_index, captions in by_source.items():
            source = scraped_data[source_index]
            source["image_captions"] = captions
            if self.embed_in_context and source.get("raw_content"):
                source["raw_content"] = (
                    source["raw_content"].rstrip()
                    + "\n\n"
                    + self._format_caption_block(captions)
                )

        if self.researcher.verbose:
            analyzed = sum(len(v) for v in by_source.values())
            await stream_output(
                "logs",
                "vision_analyzed",
                f"🖼️ Described {analyzed} relevant scraped image(s) and "
                "attached them to the research context",
                self.researcher.websocket,
            )

        return scraped_data

    def _select_images(self, scraped_data: list[dict]) -> list[dict]:
        """Pick which scraped images to analyze, deduplicated and capped.

        Args:
            scraped_data: List of scraped source dicts.

        Returns:
            Candidates as dicts with url, title and source_index keys.
        """
        if self.max_images <= 0:
            return []

        flat: list[tuple[int, float, str, str]] = []
        for source_index, source in enumerate(scraped_data):
            title = source.get("title") or ""
            for image in source.get("image_urls") or []:
                if isinstance(image, dict):
                    url = image.get("url")
                    score = float(image.get("score") or 0)
                else:
                    url = image
                    score = 0.0
                if not url or not isinstance(url, str):
                    continue
                flat.append((source_index, score, url, title))

        # Deduplicate by URL while keeping the best-ranked occurrence.
        seen_keys: set[str] = set()
        candidates: list[dict] = []
        for source_index, score, url, title in sorted(flat, key=lambda item: -item[1]):
            key = _normalize_image_key(url)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            candidates.append(
                {"url": url, "title": title, "source_index": source_index}
            )

        # Enforce per-source and global caps.
        per_source: dict[int, int] = {}
        selected: list[dict] = []
        for candidate in candidates:
            count = per_source.get(candidate["source_index"], 0)
            if count >= self.max_images_per_source:
                continue
            per_source[candidate["source_index"]] = count + 1
            selected.append(candidate)
            if len(selected) >= self.max_images:
                break
        return selected

    async def _analyze_image(
        self, url: str, title: str, query: str
    ) -> Optional[dict]:
        """Download one image and describe it with the VLM.

        Args:
            url: Image URL.
            title: Title of the page the image came from.
            query: Research query used to judge relevance.

        Returns:
            A description dict, or None when the image could not be used.
        """
        async with self._semaphore:
            try:
                image_bytes, mime_type = await self._fetch_image(url)
                return await self._describe_image(
                    image_bytes, mime_type, url, title, query
                )
            except UnsafeURLError as exc:
                logger.warning("Skipping unsafe image URL %s: %s", url, exc)
                return None
            except Exception as exc:  # noqa: BLE001 - best-effort enrichment
                logger.warning("Failed to analyze image %s: %s", url, exc)
                return None

    async def _fetch_image(self, url: str) -> tuple[bytes, str]:
        """Stream an image download, aborting once the size cap is crossed.

        Args:
            url: Image URL.

        Returns:
            Tuple of (image bytes, mime type).
        """
        validate_url(url)

        if self.image_downloader is not None:
            return await self.image_downloader(url)

        headers = {"User-Agent": "Mozilla/5.0 (compatible; gpt-researcher)"}
        timeout = httpx.Timeout(self.timeout)
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, headers=headers
        ) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_image_bytes:
                    raise ValueError(
                        f"image too large ({content_length} bytes > "
                        f"{self.max_image_bytes})"
                    )

                payload = bytearray()
                async for chunk in response.aiter_bytes():
                    payload.extend(chunk)
                    if len(payload) > self.max_image_bytes:
                        raise ValueError(
                            f"image too large (> {self.max_image_bytes} bytes)"
                        )

                if not payload:
                    raise ValueError("empty image")

                content_type = (
                    response.headers.get("content-type") or ""
                ).split(";")[0].strip()
                mime_type = content_type or _guess_mime(url)
                if not mime_type.startswith("image/"):
                    raise ValueError(
                        f"not an image (content-type: {content_type!r})"
                    )
                return bytes(payload), mime_type

    async def _describe_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        url: str,
        title: str,
        query: str,
    ) -> Optional[dict]:
        """Ask the VLM to describe one image against the research query.

        Args:
            image_bytes: Raw image bytes.
            mime_type: Image MIME type.
            url: Image URL (source attribution).
            title: Title of the page the image came from.
            query: Research sub-query.

        Returns:
            A dict with url/caption/text/relevant keys, or None if unusable.
        """
        if self.vlm_caller is not None:
            return await self.vlm_caller(
                image_bytes=image_bytes,
                mime_type=mime_type,
                url=url,
                title=title,
                query=query,
            )

        data_uri = (
            f"data:{mime_type};base64,"
            + base64.b64encode(image_bytes).decode("ascii")
        )
        user_text = _USER_PROMPT_TEMPLATE.format(
            query=query, title=title or "(unknown page)", url=url
        )
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            },
        ]
        # Same LLM layer as the rest of the project: retries, LLM_TIMEOUT,
        # provider selection and cost accounting are shared.
        content = await create_chat_completion(
            model=self.model,
            messages=messages,
            temperature=0,
            max_tokens=400,
            llm_provider=self.provider,
            llm_kwargs=self.cfg.llm_kwargs,
            cost_callback=getattr(self.researcher, "add_costs", None),
        )
        if not content:
            raise ValueError("empty VLM response")
        return self._parse_description(str(content), url, title)

    def _parse_description(self, raw_content: str, url: str, title: str) -> dict:
        """Parse the VLM answer into a normalized description dict."""
        caption = ""
        ocr_text = ""
        relevant = True
        try:
            data = json_repair.loads(raw_content)
            if isinstance(data, dict):
                caption = str(data.get("caption") or "").strip()
                ocr_text = str(data.get("text") or "").strip()
                relevant = bool(data.get("relevant", True))
        except Exception:  # noqa: BLE001 - fall back to raw text
            caption = raw_content.strip()
        if not caption:
            caption = raw_content.strip()
        return {
            "url": url,
            "title": title,
            "caption": caption,
            "text": ocr_text,
            "relevant": relevant,
        }

    def _format_caption_block(self, captions: list[dict]) -> str:
        """Render the caption block appended to a source's raw content."""
        lines = ["[Visual evidence from images in this source]"]
        for caption in captions:
            line = f"- {caption['caption']}"
            if caption.get("text"):
                line += f" Visible text: {caption['text']}"
            lines.append(line)
        block = "\n".join(lines)
        if len(block) > _CAPTION_BLOCK_MAX_CHARS:
            block = block[: _CAPTION_BLOCK_MAX_CHARS - 3].rstrip() + "..."
        return block


def _normalize_image_key(url: str) -> str:
    """Collapse URLs that only differ by tracking query/fragment."""
    return url.split("#", 1)[0].strip().lower()


def _guess_mime(url: str) -> str:
    """Guess an image MIME type from the URL suffix."""
    lower = url.lower().split("?", 1)[0]
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"
