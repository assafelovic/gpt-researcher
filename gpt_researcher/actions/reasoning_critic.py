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

from ..llm_provider.generic.base import ReasoningEfforts
from ..utils.json_parsing import parse_llm_json_response
from ..utils.language import is_german_language
from ..utils.llm import create_chat_completion
from ..utils.logger import get_formatted_logger
from .verification import build_verification_bundle

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


def _critic_fallback_text(language: str | None) -> dict[str, str]:
    if is_german_language(language):
        return {
            "issue_problem": "Die Aussage wird durch das verfügbare Evidenzpaket nicht direkt gestützt.",
            "issue_fix": "Fügen Sie einen Vorbehalt hinzu, nennen Sie eine Quelle mit direkter Evidenz oder streichen Sie die Aussage.",
            "partial_problem": "Die Aussage ist nur teilweise gestützt und sollte vorsichtiger formuliert werden.",
            "partial_fix": "Formulieren Sie enger, ergänzen Sie Vorbehalte oder stärken Sie die Evidenzkette.",
            "support_strength": "{count} Aussagen werden direkt durch das Evidenzpaket gestützt.",
            "support_rate": "Die Verifikationsabdeckung liegt bei {rate:.0%}.",
            "no_unsupported": "Der deterministische Prüfer hat keine klar ungestützten Aussagen festgestellt.",
            "verification_appendix": "Der Bericht enthält bereits einen Verifikationsanhang.",
            "recommendation_support": "Priorisieren Sie Aussagen mit direkter Quellenbelegung und expliziten Zitaten.",
            "recommendation_partial": "Formulieren Sie mehrdeutige Aussagen als Hypothesen oder Vorbehalte, wenn die Evidenz nur teilweise ist.",
            "recommendation_manual_review": "Erfordern Sie eine manuelle Prüfung, bevor der Bericht für sensible Entscheidungen verwendet wird.",
            "summary_high": "Der Bericht wirkt risikoreich und sollte manuell geprüft werden.",
            "summary_revise": "Der Bericht wirkt inhaltlich brauchbar, sollte aber vor der Nutzung gestrafft werden.",
            "summary_pass": "Der Bericht ist auf Basis der verfügbaren Evidenz akzeptabel.",
            "summary_default": "Der Begründungskritiker hat den Bericht und den Verifikationsanhang geprüft.",
        }

    return {
        "issue_problem": "Claim is not directly supported by the available evidence bundle.",
        "issue_fix": "Add a caveat, cite a source with direct evidence, or remove the claim.",
        "partial_problem": "Claim is only partially supported and should be framed more carefully.",
        "partial_fix": "Narrow the wording, add qualifiers, or strengthen the evidence chain.",
        "support_strength": "{count} claims are directly supported by the evidence bundle.",
        "support_rate": "Verification support rate is {rate:.0%}.",
        "no_unsupported": "No outright unsupported claims were detected by the deterministic critic.",
        "verification_appendix": "The report already includes a verification appendix.",
        "recommendation_support": "Prioritize claims with direct source support and explicit citations.",
        "recommendation_partial": "Reframe ambiguous statements as hypotheses or caveats when evidence is partial.",
        "recommendation_manual_review": "Require manual review before using the report for sensitive decisions.",
        "summary_high": "The report appears high-risk and should be reviewed manually.",
        "summary_revise": "The report appears directionally sound but should be tightened before relying on it.",
        "summary_pass": "The report is acceptable from the available evidence.",
        "summary_default": "The critic reviewed the report and verification bundle.",
    }


def _deterministic_critic_bundle(
    query: str,
    report_markdown: str,
    verification_bundle: dict[str, Any],
    language: str | None = None,
) -> dict[str, Any]:
    summary = verification_bundle.get("summary", {})
    risk = verification_bundle.get("risk", {})
    claims = verification_bundle.get("claims", [])
    text = _critic_fallback_text(language)

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
                "problem": text["issue_problem"],
                "evidence": [source.get("source_url") or source.get("source_id") for source in claim.get("sources", [])[:3]],
                "suggested_fix": text["issue_fix"],
            }
        )

    for claim in partial[:2]:
        issues.append(
            {
                "severity": "medium",
                "claim": claim.get("claim"),
                "problem": text["partial_problem"],
                "evidence": [source.get("source_url") or source.get("source_id") for source in claim.get("sources", [])[:3]],
                "suggested_fix": text["partial_fix"],
            }
        )

    strengths = [
        text["support_strength"].format(count=len(supported)),
        text["support_rate"].format(rate=support_rate),
    ]
    if not unsupported:
        strengths.append(text["no_unsupported"])

    if "## Verification Review" in report_markdown or "## Verifikationsprüfung" in report_markdown:
        strengths.append(text["verification_appendix"])

    recommendations = [
        text["recommendation_support"],
        text["recommendation_partial"],
    ]
    if human_review_required:
        recommendations.append(text["recommendation_manual_review"])

    confidence = 0.9 if verdict == "pass" else 0.72 if verdict == "revise" else 0.88

    return {
        "source": "deterministic",
        "verdict": verdict,
        "confidence": confidence,
        "summary": text["summary_high"] if verdict == "high_risk" else text["summary_revise"] if verdict == "revise" else text["summary_pass"],
        "issues": issues,
        "strengths": strengths,
        "recommendations": recommendations,
    }


def _parse_critic_payload(response: str | None) -> dict[str, Any] | None:
    payload = parse_llm_json_response(response, expected_kind="object")
    return payload if isinstance(payload, dict) else None


def _normalize_critic_payload(
    payload: dict[str, Any],
    fallback_bundle: dict[str, Any],
    language: str | None = None,
) -> dict[str, Any]:
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
        text = _critic_fallback_text(language)
        strengths = [
            text["support_strength"].format(
                count=fallback_bundle.get("summary", {}).get("supported_claims", 0)
            )
        ]

    recommendations = [
        str(item)
        for item in _coerce_list(payload.get("recommendations"))[:6]
        if str(item).strip()
    ]
    if not recommendations:
        text = _critic_fallback_text(language)
        recommendations = [
            text["recommendation_support"],
            text["recommendation_partial"],
        ]
        if fallback_bundle.get("risk", {}).get("human_review_required"):
            recommendations.append(text["recommendation_manual_review"])

    confidence_raw = payload.get("confidence", 0.7)
    try:
        confidence = max(0.0, min(1.0, float(confidence_raw)))
    except Exception:
        confidence = 0.7

    summary = str(payload.get("summary") or payload.get("rationale") or "").strip()
    if not summary:
        summary = _critic_fallback_text(language)["summary_default"]

    return {
        "source": "llm",
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "issues": issues,
        "strengths": strengths,
        "recommendations": recommendations,
    }


def _critic_text(language: str | None) -> dict[str, str]:
    if is_german_language(language):
        return {
            "title": "## Begründungskritik",
            "verdict": "Urteil",
            "confidence": "Vertrauen",
            "source": "Quelle",
            "summary": "Zusammenfassung",
            "strengths": "### Stärken",
            "issues": "### Probleme",
            "recommendations": "### Empfehlungen",
            "suggested_fix": "Vorgeschlagene Korrektur",
            "no_issues": "- Es wurden keine konkreten Begründungsprobleme identifiziert.",
            "high_risk_note": "### Hinweis auf hohes Risiko",
            "high_risk_text": "- Der Bericht sollte manuell geprüft werden, bevor auf ihn bei sensiblen Entscheidungen vertraut wird.",
            "pass": "bestanden",
            "revise": "überarbeiten",
            "high_risk": "hohes Risiko",
            "claim": "Aussage",
            "evidence": "Beleg",
            "no_evidence": "kein expliziter Beleg",
        }

    return {
        "title": "## Reasoning Critic",
        "verdict": "Verdict",
        "confidence": "Confidence",
        "source": "Source",
        "summary": "Summary",
        "strengths": "### Strengths",
        "issues": "### Issues",
        "recommendations": "### Recommendations",
        "suggested_fix": "Suggested fix",
        "no_issues": "- No concrete reasoning issues were identified.",
        "high_risk_note": "### High Risk Note",
        "high_risk_text": "- The report should be manually reviewed before relying on it for sensitive decisions.",
        "pass": "pass",
        "revise": "revise",
        "high_risk": "high_risk",
        "claim": "claim",
        "evidence": "evidence",
        "no_evidence": "no explicit evidence",
    }


def render_reasoning_critic_section(bundle: dict[str, Any], language: str = "english") -> str:
    """Render a markdown appendix for the reasoning critic."""
    verdict = bundle.get("verdict", "revise")
    confidence = float(bundle.get("confidence", 0.0) or 0.0)
    summary = _normalize_whitespace(str(bundle.get("summary", "")))
    issues = bundle.get("issues", []) or []
    strengths = bundle.get("strengths", []) or []
    recommendations = bundle.get("recommendations", []) or []
    text = _critic_text(language)
    verdict_label = text.get(verdict, verdict)

    lines: list[str] = [
        text["title"],
        f"- {text['verdict']}: {verdict_label}",
        f"- {text['confidence']}: {confidence:.0%}",
        f"- {text['source']}: {bundle.get('source', 'unknown')}",
    ]

    if summary:
        lines.append(f"- {text['summary']}: {summary}")

    if strengths:
        lines.extend(["", text["strengths"]])
        for strength in strengths[:6]:
            lines.append(f"- {strength}")

    if issues:
        lines.extend(["", text["issues"]])
        for issue in issues[:8]:
            if not isinstance(issue, dict):
                lines.append(f"- {issue}")
                continue
            evidence = _coerce_list(issue.get("evidence"))[:3]
            evidence_text = ", ".join(str(item) for item in evidence if str(item).strip()) or text["no_evidence"]
            lines.append(
                f"- {issue.get('severity', 'medium').upper()}: {issue.get('problem', '')} "
                f"({text['claim']}: {issue.get('claim', 'n/a')}; {text['evidence']}: {evidence_text})"
            )
            suggestion = issue.get("suggested_fix")
            if suggestion:
                lines.append(f"  - {text['suggested_fix']}: {suggestion}")
    else:
        lines.extend(["", text["issues"], text["no_issues"]])

    if recommendations:
        lines.extend(["", text["recommendations"]])
        for recommendation in recommendations[:6]:
            lines.append(f"- {recommendation}")

    if verdict == "high_risk":
        lines.extend(
            [
                "",
                text["high_risk_note"],
                text["high_risk_text"],
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
    language: str | None = None,
    websocket=None,
    cost_callback: callable = None,
    **kwargs,
) -> dict[str, Any]:
    """Build a structured LLM-backed critique of the report."""
    del websocket

    # Keep internal research metadata out of the provider call surface.
    # Some backends reject unexpected keyword arguments such as visited_urls.
    llm_call_kwargs = {key: value for key, value in kwargs.items() if key != "visited_urls"}

    if verification_bundle is None:
        verification_bundle = build_verification_bundle(
            query=query,
            context=context,
            report_markdown=report_markdown,
            visited_urls=kwargs.get("visited_urls"),
            language=language,
        )

    if not getattr(cfg, "enable_reasoning_critic", True):
        return _deterministic_critic_bundle(query, report_markdown, verification_bundle, language=language)

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

    if is_german_language(language):
        prompt += (
            "\nRespond in German. Use German phrasing for the summary, issues, strengths, and recommendations, "
            "but keep the JSON keys exactly as specified."
        )

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
            **llm_call_kwargs,
        )
        payload = _parse_critic_payload(response)
        if payload:
            payload["raw_response"] = response
            normalized = _normalize_critic_payload(payload, verification_bundle, language=language)
            return normalized
        logger.warning("LLM critic response could not be parsed; using deterministic fallback.")
    except Exception as exc:
        logger.warning("Reasoning critic failed, using deterministic fallback: %s", exc, exc_info=True)

    return _deterministic_critic_bundle(query, report_markdown, verification_bundle, language=language)
