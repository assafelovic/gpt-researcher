"""LLM-backed reasoning critic for GPT Researcher reports.

The critic reviews the generated report against the verification bundle and
returns a structured assessment of unsupported claims, missing caveats, and
high-risk situations. If the LLM response cannot be parsed, the module falls
back to a deterministic review based on the verification summary.
"""

from __future__ import annotations

import json
import re
from typing import Any

import json_repair

from .agent_creator import extract_json_with_regex
from .verification import build_verification_bundle
from ..llm_provider.generic.base import ReasoningEfforts
from ..utils.llm import create_chat_completion
from ..utils.logger import get_formatted_logger

logger = get_formatted_logger()


def _normalize_whitespace(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    if isinstance(value, str):
        lines = [
            line.strip("-• \t")
            for line in value.splitlines()
            if line.strip()
        ]
        return lines or [value]
    return [value]


def _compact_verification_payload(bundle: dict[str, Any], max_claims: int = 8) -> dict[str, Any]:
    claims = []
    for claim in bundle.get("claims", [])[:max_claims]:
        claims.append(
            {
                "id": claim.get("id"),
                "claim": claim.get("claim"),
                "status": claim.get("status"),
                "confidence": claim.get("confidence"),
                "source_count": len(claim.get("sources", [])),
            }
        )

    return {
        "query": bundle.get("query"),
        "risk": bundle.get("risk", {}),
        "summary": bundle.get("summary", {}),
        "claims": claims,
    }


def _deterministic_critic_bundle(
    query: str,
    report_markdown: str,
    verification_bundle: dict[str, Any],
) -> dict[str, Any]:
    summary = verification_bundle.get("summary", {})
    risk = verification_bundle.get("risk", {})
    claims = verification_bundle.get("claims", [])

    unsupported = [claim for claim in claims if claim.get("status") == "unsupported"]
    partial = [claim for claim in claims if claim.get("status") == "partial"]
    supported = [claim for claim in claims if claim.get("status") == "supported"]

    support_rate = float(summary.get("support_rate", 0.0) or 0.0)
    human_review_required = bool(risk.get("human_review_required"))

    if human_review_required or risk.get("level") == "high":
        verdict = "high_risk"
    elif unsupported or support_rate < 0.75:
        verdict = "revise"
    else:
        verdict = "pass"

    issues: list[dict[str, Any]] = []
    for claim in unsupported[:4]:
        issues.append(
            {
                "severity": "high" if human_review_required else "medium",
                "claim": claim.get("claim"),
                "problem": "Claim is not directly supported by the available evidence bundle.",
                "evidence": [source.get("source_url") or source.get("source_id") for source in claim.get("sources", [])[:3]],
                "suggested_fix": "Add a caveat, cite a source with direct evidence, or remove the claim.",
            }
        )

    for claim in partial[:2]:
        issues.append(
            {
                "severity": "medium",
                "claim": claim.get("claim"),
                "problem": "Claim is only partially supported and should be framed more carefully.",
                "evidence": [source.get("source_url") or source.get("source_id") for source in claim.get("sources", [])[:3]],
                "suggested_fix": "Narrow the wording, add qualifiers, or strengthen the evidence chain.",
            }
        )

    strengths = [
        f"{len(supported)} claims are directly supported by the evidence bundle.",
        f"Verification support rate is {support_rate:.0%}.",
    ]
    if not unsupported:
        strengths.append("No outright unsupported claims were detected by the deterministic critic.")

    if "## Verification Review" in report_markdown:
        strengths.append("The report already includes a verification appendix.")

    recommendations = [
        "Prioritize claims with direct source support and explicit citations.",
        "Reframe ambiguous statements as hypotheses or caveats when evidence is partial.",
    ]
    if human_review_required:
        recommendations.append("Require manual review before using the report for sensitive decisions.")

    confidence = 0.9 if verdict == "pass" else 0.72 if verdict == "revise" else 0.88

    return {
        "source": "deterministic",
        "verdict": verdict,
        "confidence": confidence,
        "summary": (
            "The report appears "
            + ("high-risk and should be reviewed manually." if verdict == "high_risk" else "directionally sound but should be tightened before relying on it." if verdict == "revise" else "acceptable from the available evidence.")
        ),
        "issues": issues,
        "strengths": strengths,
        "recommendations": recommendations,
    }


def _parse_critic_payload(response: str | None) -> dict[str, Any] | None:
    if not response:
        return None

    candidates = [response]
    if json_fragment := extract_json_with_regex(response):
        candidates.append(json_fragment)

    for candidate in candidates:
        for loader in (json.loads, json_repair.loads):
            try:
                payload = loader(candidate)
            except Exception:
                continue

            if isinstance(payload, dict):
                return payload

    return None


def _normalize_critic_payload(payload: dict[str, Any], fallback_bundle: dict[str, Any]) -> dict[str, Any]:
    verdict = str(payload.get("verdict") or payload.get("status") or "revise").strip().lower()
    if verdict not in {"pass", "revise", "high_risk"}:
        verdict = "revise"

    issues = []
    for issue in _coerce_list(payload.get("issues"))[:8]:
        if isinstance(issue, dict):
            issues.append(
                {
                    "severity": str(issue.get("severity") or "medium").strip().lower(),
                    "claim": issue.get("claim"),
                    "problem": issue.get("problem") or issue.get("issue") or "",
                    "evidence": _coerce_list(issue.get("evidence"))[:3],
                    "suggested_fix": issue.get("suggested_fix") or issue.get("fix") or "",
                }
            )
        else:
            issues.append(
                {
                    "severity": "medium",
                    "claim": None,
                    "problem": str(issue),
                    "evidence": [],
                    "suggested_fix": "",
                }
            )

    strengths = [str(item) for item in _coerce_list(payload.get("strengths"))[:6] if str(item).strip()]
    if not strengths:
        strengths = [
            f"{fallback_bundle.get('summary', {}).get('supported_claims', 0)} claims are supported by the evidence bundle."
        ]

    recommendations = [
        str(item)
        for item in _coerce_list(payload.get("recommendations"))[:6]
        if str(item).strip()
    ]
    if not recommendations:
        recommendations = [
            "Preserve the verification appendix and tighten unsupported claims.",
        ]

    confidence_raw = payload.get("confidence", 0.7)
    try:
        confidence = max(0.0, min(1.0, float(confidence_raw)))
    except Exception:
        confidence = 0.7

    summary = str(payload.get("summary") or payload.get("rationale") or "").strip()
    if not summary:
        summary = "The critic reviewed the report and verification bundle."

    return {
        "source": "llm",
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "issues": issues,
        "strengths": strengths,
        "recommendations": recommendations,
    }


def render_reasoning_critic_section(bundle: dict[str, Any]) -> str:
    """Render a markdown appendix for the reasoning critic."""
    verdict = bundle.get("verdict", "revise")
    confidence = float(bundle.get("confidence", 0.0) or 0.0)
    summary = _normalize_whitespace(str(bundle.get("summary", "")))
    issues = bundle.get("issues", []) or []
    strengths = bundle.get("strengths", []) or []
    recommendations = bundle.get("recommendations", []) or []

    lines: list[str] = [
        "## Reasoning Critic",
        f"- Verdict: {verdict}",
        f"- Confidence: {confidence:.0%}",
        f"- Source: {bundle.get('source', 'unknown')}",
    ]

    if summary:
        lines.append(f"- Summary: {summary}")

    if strengths:
        lines.extend(["", "### Strengths"])
        for strength in strengths[:6]:
            lines.append(f"- {strength}")

    if issues:
        lines.extend(["", "### Issues"])
        for issue in issues[:8]:
            if not isinstance(issue, dict):
                lines.append(f"- {issue}")
                continue
            evidence = _coerce_list(issue.get("evidence"))[:3]
            evidence_text = ", ".join(str(item) for item in evidence if str(item).strip()) or "no explicit evidence"
            lines.append(
                f"- {issue.get('severity', 'medium').upper()}: {issue.get('problem', '')} "
                f"(claim: {issue.get('claim', 'n/a')}; evidence: {evidence_text})"
            )
            suggestion = issue.get("suggested_fix")
            if suggestion:
                lines.append(f"  - Suggested fix: {suggestion}")
    else:
        lines.extend(["", "### Issues", "- No concrete reasoning issues were identified."])

    if recommendations:
        lines.extend(["", "### Recommendations"])
        for recommendation in recommendations[:6]:
            lines.append(f"- {recommendation}")

    if verdict == "high_risk":
        lines.extend(
            [
                "",
                "### High Risk Note",
                "- The report should be manually reviewed before relying on it for sensitive decisions.",
            ]
        )

    return "\n".join(lines).strip()


async def build_reasoning_critic_bundle(
    query: str,
    context: str,
    report_markdown: str,
    verification_bundle: dict[str, Any] | None,
    cfg,
    agent_role_prompt: str,
    websocket=None,
    cost_callback: callable = None,
    **kwargs,
) -> dict[str, Any]:
    """Build a structured LLM-backed critique of the report."""
    del websocket

    if verification_bundle is None:
        verification_bundle = build_verification_bundle(
            query=query,
            context=context,
            report_markdown=report_markdown,
            visited_urls=kwargs.get("visited_urls"),
        )

    if not getattr(cfg, "enable_reasoning_critic", True):
        return _deterministic_critic_bundle(query, report_markdown, verification_bundle)

    compact_bundle = _compact_verification_payload(verification_bundle)
    report_excerpt = report_markdown[:7000]

    prompt = f"""You are a skeptical senior research editor.

Review the research report against the verification bundle and identify only real problems.
Your job is to catch unsupported claims, contradictions, missing caveats, overconfident language,
and high-risk issues. Do not invent problems that are not grounded in the report or evidence.

RESEARCH QUERY:
{query}

REPORT EXCERPT:
{report_excerpt}

VERIFICATION BUNDLE:
{json.dumps(compact_bundle, indent=2, ensure_ascii=False)}

Return ONLY valid JSON with this exact shape:
{{
  "verdict": "pass|revise|high_risk",
  "confidence": 0.0,
  "summary": "short summary of the overall assessment",
  "issues": [
    {{
      "severity": "low|medium|high",
      "claim": "claim text",
      "problem": "what is wrong or unclear",
      "evidence": ["supporting claim id or source url"],
      "suggested_fix": "how to repair the issue"
    }}
  ],
  "strengths": ["positive observations"],
  "recommendations": ["actionable edits"]
}}

Be strict but fair. If the report is acceptable, say so directly with verdict "pass".
"""

    model = getattr(cfg, "smart_llm_model", None) or getattr(cfg, "strategic_llm_model", None)
    provider = getattr(cfg, "smart_llm_provider", None) or getattr(cfg, "strategic_llm_provider", None)
    max_tokens = min(
        int(getattr(cfg, "smart_token_limit", 4000) or 4000),
        int(getattr(cfg, "reasoning_critic_max_tokens", 1200) or 1200),
    )
    temperature = float(getattr(cfg, "reasoning_critic_temperature", 0.1) or 0.1)

    try:
        response = await create_chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": agent_role_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            llm_provider=provider,
            stream=True,
            websocket=None,
            max_tokens=max_tokens,
            llm_kwargs=getattr(cfg, "llm_kwargs", {}),
            cost_callback=cost_callback,
            reasoning_effort=ReasoningEfforts.High.value,
            **kwargs,
        )
        payload = _parse_critic_payload(response)
        if payload:
            payload["raw_response"] = response
            normalized = _normalize_critic_payload(payload, verification_bundle)
            return normalized
        logger.warning("LLM critic response could not be parsed; using deterministic fallback.")
    except Exception as exc:
        logger.warning("Reasoning critic failed, using deterministic fallback: %s", exc, exc_info=True)

    return _deterministic_critic_bundle(query, report_markdown, verification_bundle)
