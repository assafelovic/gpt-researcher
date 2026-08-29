"""Source assessor skill for GPT Researcher.

This module provides an optional admission-policy gate for scraped sources.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import json_repair

from ..utils.llm import create_chat_completion

logger = logging.getLogger(__name__)

JSON_BLOCK_PATTERNS = [
    re.compile(
        r"```(?:json)?\s*(?P<payload>[\s\S]*?)```",
        re.IGNORECASE,
    ),
    re.compile(r"(?P<payload>\{[\s\S]*\})"),
]


class SourceAssessor:
    """Evaluates scraped sources against a caller-provided policy."""

    def __init__(self, researcher):
        """Initialize the SourceAssessor.

        Args:
            researcher: The GPTResearcher instance that owns this assessor.
        """
        self.researcher = researcher

    async def assess_sources(
        self,
        scraped_sources: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Assess scraped sources and return accepted sources plus rejected records."""
        if not scraped_sources:
            return [], []

        concurrency = max(
            1,
            int(getattr(self.researcher, "source_assessment_max_concurrency", 4) or 1),
        )
        semaphore = asyncio.Semaphore(concurrency)

        async def assess_with_limit(source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
            async with semaphore:
                return source, await self._assess_source(source)

        results = await asyncio.gather(
            *(assess_with_limit(source) for source in scraped_sources)
        )

        accepted_sources = []
        assessments = []
        rejected_sources = []
        for source, assessment in results:
            assessments.append(assessment)
            if assessment["accepted"]:
                accepted_sources.append(source)
            else:
                rejected_sources.append(assessment)

        self.researcher.add_source_assessments(assessments)
        return accepted_sources, rejected_sources

    async def _assess_source(self, source: dict[str, Any]) -> dict[str, Any]:
        url = str(source.get("url") or source.get("href") or "")
        title = str(source.get("title") or "")

        try:
            response = await create_chat_completion(
                model=self.researcher.cfg.fast_llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You score how much a source violates a caller-provided admission policy. "
                            "score is a float in [0.0, 1.0]: 0.0 means no violation, 1.0 means complete violation. "
                            "Return only JSON with keys: score, reason, matched_policy."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_assessment_prompt(source),
                    },
                ],
                temperature=0.0,
                max_tokens=self.researcher.cfg.fast_token_limit,
                llm_provider=self.researcher.cfg.fast_llm_provider,
                llm_kwargs=getattr(self.researcher.cfg, "llm_kwargs", None),
                cost_callback=getattr(self.researcher, "add_costs", None),
            )
            parsed = _load_repaired_json(response)
            if not isinstance(parsed, dict):
                return self._rejected_assessment(
                    url,
                    title,
                    "Source assessment failed: response was not a JSON object.",
                )

            score = _coerce_score(parsed.get("score"))
            if score is None:
                return self._rejected_assessment(
                    url,
                    title,
                    "Source assessment failed: score must be a float in [0.0, 1.0].",
                )

            threshold = float(getattr(self.researcher, "source_assessment_threshold", 0.25))
            accepted = score <= threshold
            return {
                "url": url,
                "title": title,
                "accepted": accepted,
                "score": score,
                "reason": str(parsed.get("reason") or ""),
                "matched_policy": str(parsed.get("matched_policy") or ""),
            }
        except Exception as exc:
            logger.warning("Source assessment failed for %s: %s", url, exc)
            return self._rejected_assessment(
                url,
                title,
                f"Source assessment failed: {exc}",
            )

    def _build_assessment_prompt(self, source: dict[str, Any]) -> str:
        max_chars = int(getattr(self.researcher, "source_assessment_max_content_chars", 12000))
        raw_content = str(source.get("raw_content") or "")
        if max_chars >= 0:
            raw_content = raw_content[:max_chars]

        return "\n".join(
            [
                "Score how much this source violates SOURCE_ADMISSION_POLICY.",
                "score is a float in [0.0, 1.0]: 0.0 means no violation, 1.0 means complete violation.",
                "reason explains the violation or why there is none.",
                "matched_policy names the policy clause that drove the score.",
                "",
                "SOURCE_ADMISSION_POLICY:",
                getattr(self.researcher, "source_assessment_prompt", None) or "",
                "",
                "SOURCE:",
                f"url: {source.get('url') or source.get('href') or ''}",
                f"title: {source.get('title') or ''}",
                "",
                "RAW_CONTENT:",
                raw_content,
                "",
                "Return JSON only:",
                '{"score": 0.0, "reason": "", "matched_policy": ""}',
            ]
        )

    def _rejected_assessment(self, url: str, title: str, reason: str) -> dict[str, Any]:
        return {
            "url": url,
            "title": title,
            "accepted": False,
            "score": 0.0,
            "reason": reason,
            "matched_policy": "assessment_failure",
        }


def _extract_json_payloads(response: str) -> list[str]:
    candidates = []
    seen = set()
    for pattern in JSON_BLOCK_PATTERNS:
        for match in pattern.finditer(response):
            candidate = match.group("payload").strip()
            if candidate and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)
    return candidates


def _load_repaired_json(response: str) -> Any:
    for candidate in [response.strip(), *_extract_json_payloads(response)]:
        if not candidate:
            continue
        try:
            return json_repair.loads(candidate)
        except Exception as exc:
            logger.debug(
                "json_repair failed on source assessment candidate (%d chars): %s",
                len(candidate),
                exc,
            )
    return None


def _coerce_score(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0.0 or score > 1.0:
        return None
    return score
