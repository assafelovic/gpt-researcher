"""Verification helpers for GPT Researcher reports.

This module builds a lightweight claim ledger, evidence graph, and risk
summary for a generated report. The goal is not to guarantee truth, but to
make support, uncertainty, and escalation visible by default.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

_STOPWORDS = {
    "a",
    "about",
    "across",
    "after",
    "against",
    "all",
    "also",
    "an",
    "and",
    "around",
    "as",
    "at",
    "be",
    "because",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "do",
    "does",
    "done",
    "during",
    "each",
    "for",
    "from",
    "give",
    "given",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "more",
    "most",
    "must",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "overview",
    "please",
    "practical",
    "report",
    "result",
    "results",
    "review",
    "should",
    "summary",
    "task",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "through",
    "to",
    "today",
    "topic",
    "was",
    "we",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "with",
    "without",
    "would",
}

_RISK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "health": (
        "diagnosis",
        "disease",
        "medical",
        "medicine",
        "medication",
        "prescription",
        "symptom",
        "treatment",
        "therapy",
        "vaccine",
        "surgery",
        "dose",
        "dosage",
        "cancer",
        "suicide",
        "self-harm",
        "mental health",
    ),
    "legal": (
        "legal",
        "law",
        "lawsuit",
        "attorney",
        "court",
        "contract",
        "liability",
        "regulation",
        "compliance",
        "litigation",
        "tax",
    ),
    "finance": (
        "invest",
        "investment",
        "stock",
        "stocks",
        "bond",
        "crypto",
        "cryptocurrency",
        "portfolio",
        "trading",
        "financial",
        "mortgage",
        "loan",
        "earnings",
        "market",
    ),
    "security": (
        "exploit",
        "vulnerability",
        "malware",
        "ransomware",
        "breach",
        "hack",
        "hacking",
        "phishing",
        "password",
        "weapon",
        "bomb",
    ),
    "politics": (
        "election",
        "government",
        "vote",
        "campaign",
        "policy",
        "sanction",
        "war",
        "military",
        "president",
        "senate",
        "congress",
        "diplomacy",
    ),
}

_HIGH_RISK_CATEGORIES = {"health", "legal", "finance", "security"}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower()).strip()


def _extract_terms(text: str | None) -> list[str]:
    if not text:
        return []

    terms: list[str] = []
    seen: set[str] = set()
    for raw_token in re.findall(r"[A-Za-z0-9]+", text):
        normalized = _normalize_token(raw_token)
        if not normalized or normalized in _STOPWORDS:
            continue
        if len(normalized) == 1 and not normalized.isdigit():
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        terms.append(normalized)
    return terms


def _extract_urls(text: str | None) -> list[str]:
    if not text:
        return []

    seen: set[str] = set()
    urls: list[str] = []
    for match in re.findall(r"https?://[^\s)\]>,]+", text):
        url = match.rstrip(".,;:")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _split_chunks(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n+", text or "") if chunk.strip()]


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []

    sentences: list[str] = []
    for chunk in _split_chunks(text):
        pieces = re.split(r"(?<=[.!?])\s+|\n+", chunk)
        for piece in pieces:
            sentence = _normalize_whitespace(piece)
            if len(sentence.split()) >= 6:
                sentences.append(sentence)
    return sentences


def _collect_report_claim_candidates(report_markdown: str, max_claims: int = 12) -> list[str]:
    if not report_markdown:
        return []

    analysis_text = report_markdown.split("## Verification Review", 1)[0]
    candidates: list[str] = []
    seen: set[str] = set()

    for line in analysis_text.splitlines():
        stripped = _normalize_whitespace(line)
        if not stripped or stripped.startswith("#"):
            continue

        lowered = stripped.lower()
        if lowered.startswith("references") or lowered.startswith("- no explicit source urls"):
            continue
        if lowered.startswith("human review"):
            continue

        if re.match(r"^[-*•]\s+", stripped):
            stripped = re.sub(r"^[-*•]\s+", "", stripped).strip()
        elif re.match(r"^\d+[\.\)]\s+", stripped):
            stripped = re.sub(r"^\d+[\.\)]\s+", "", stripped).strip()

        if len(stripped.split()) < 5:
            continue

        key = stripped.lower()
        if key in seen:
            continue

        seen.add(key)
        candidates.append(stripped)
        if len(candidates) >= max_claims:
            return candidates

    if len(candidates) < max_claims:
        for sentence in _split_sentences(analysis_text):
            key = sentence.lower()
            if key in seen or len(sentence.split()) < 8:
                continue
            seen.add(key)
            candidates.append(sentence)
            if len(candidates) >= max_claims:
                break

    return candidates[:max_claims]


def _risk_keywords_for_text(text: str | None) -> dict[str, list[str]]:
    lowered = (text or "").lower()
    matched: dict[str, list[str]] = {}

    for category, keywords in _RISK_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in lowered]
        if hits:
            matched[category] = hits

    return matched


def classify_risk(query: str, report_markdown: str, claims: list[str] | None = None) -> dict[str, Any]:
    """Classify the topic risk for human review purposes."""
    combined_text = f"{query}\n{report_markdown}"
    claim_text = "\n".join(claims or [])
    combined_hits = _risk_keywords_for_text(combined_text)
    claim_hits = _risk_keywords_for_text(claim_text)

    matched = combined_hits or claim_hits
    categories = list(matched.keys())

    if any(category in _HIGH_RISK_CATEGORIES for category in categories):
        level = "high"
    elif categories:
        level = "medium"
    else:
        level = "low"

    if not categories:
        reason = "No high-risk keywords were detected in the query or report."
    else:
        parts = []
        for category, hits in matched.items():
            parts.append(f"{category}: {', '.join(hits[:4])}")
        reason = "; ".join(parts)

    return {
        "level": level,
        "categories": categories,
        "reason": reason,
        "human_review_required": level in {"medium", "high"},
    }


def _required_term_overlap(claim_terms: list[str]) -> int:
    if len(claim_terms) <= 4:
        return 1
    if len(claim_terms) <= 8:
        return 2
    return 3


def _best_source_label(source_urls: list[str], fallback_index: int) -> tuple[str, str | None]:
    if source_urls:
        url = source_urls[0]
        return url, url
    source_id = f"chunk:{fallback_index}"
    return source_id, None


def _score_claim_against_chunk(claim: str, chunk: str) -> tuple[float, bool, list[str]]:
    claim_terms = _extract_terms(claim)
    chunk_terms = set(_extract_terms(chunk))
    overlap = [term for term in claim_terms if term in chunk_terms]
    numeric_claims = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim)
    numeric_hits = [value for value in numeric_claims if value in chunk]

    if not claim_terms:
        return 0.0, False, numeric_hits

    overlap_ratio = len(overlap) / len(claim_terms)
    threshold = _required_term_overlap(claim_terms)
    strong_match = len(overlap) >= threshold or bool(numeric_hits)
    score = overlap_ratio
    if numeric_hits:
        score = min(1.0, score + 0.35)
    if strong_match:
        score = min(1.0, score + 0.25)

    return score, strong_match, numeric_hits


def build_verification_bundle(
    query: str,
    context: str,
    report_markdown: str,
    visited_urls: list[str] | None = None,
    max_claims: int = 12,
) -> dict[str, Any]:
    """Build a structured verification bundle for a generated report."""
    visited_urls = list(dict.fromkeys(visited_urls or []))
    claim_candidates = _collect_report_claim_candidates(report_markdown, max_claims=max_claims)
    claim_entries: list[dict[str, Any]] = []
    evidence_nodes: list[dict[str, Any]] = []
    evidence_edges: list[dict[str, Any]] = []
    source_nodes: dict[str, dict[str, Any]] = {}

    if context:
        context_chunks = _split_chunks(context)
    else:
        context_chunks = []

    if not context_chunks and report_markdown:
        context_chunks = _split_chunks(report_markdown)

    for claim_index, claim in enumerate(claim_candidates, 1):
        claim_node_id = f"claim:{claim_index}"
        claim_terms = _extract_terms(claim)
        supporting_sources: list[dict[str, Any]] = []
        strong_support_count = 0
        partial_support_count = 0

        for chunk_index, chunk in enumerate(context_chunks, 1):
            score, strong_match, numeric_hits = _score_claim_against_chunk(claim, chunk)
            if score < 0.35:
                continue

            chunk_urls = _extract_urls(chunk)
            if not chunk_urls and visited_urls:
                chunk_urls = visited_urls[:2]

            source_id, source_url = _best_source_label(chunk_urls, chunk_index)
            if source_id not in source_nodes:
                source_nodes[source_id] = {
                    "id": source_id,
                    "type": "source",
                    "label": source_url or source_id,
                    "url": source_url,
                    "evidence_preview": _normalize_whitespace(chunk)[:280],
                }

            evidence_preview = _normalize_whitespace(chunk)[:280]
            supporting_sources.append(
                {
                    "source_id": source_id,
                    "source_url": source_url,
                    "score": round(score, 3),
                    "evidence_preview": evidence_preview,
                    "numeric_hits": numeric_hits,
                }
            )
            evidence_edges.append(
                {
                    "from": claim_node_id,
                    "to": source_id,
                    "type": "supports" if strong_match else "partial_support",
                    "score": round(score, 3),
                    "evidence_preview": evidence_preview,
                }
            )

            if strong_match:
                strong_support_count += 1
            else:
                partial_support_count += 1

            if strong_support_count + partial_support_count >= 4:
                break

        if strong_support_count >= 2:
            status = "supported"
            confidence = 0.9
        elif strong_support_count == 1 or partial_support_count >= 2:
            status = "partial"
            confidence = 0.6
        elif supporting_sources:
            status = "partial"
            confidence = 0.45
        else:
            status = "unsupported"
            confidence = 0.1

        claim_entries.append(
            {
                "id": claim_node_id,
                "claim": claim,
                "terms": claim_terms,
                "status": status,
                "confidence": confidence,
                "support_count": strong_support_count,
                "partial_support_count": partial_support_count,
                "sources": supporting_sources,
            }
        )
        evidence_nodes.append(
            {
                "id": claim_node_id,
                "type": "claim",
                "label": claim,
            }
        )

    query_node_id = "query:0"
    evidence_nodes.insert(
        0,
        {
            "id": query_node_id,
            "type": "query",
            "label": query,
        },
    )

    for claim in claim_entries:
        evidence_edges.append(
            {
                "from": query_node_id,
                "to": claim["id"],
                "type": "focuses",
                "score": 1.0,
            }
        )

    for source_node in source_nodes.values():
        evidence_nodes.append(source_node)

    supported_count = sum(1 for claim in claim_entries if claim["status"] == "supported")
    partial_count = sum(1 for claim in claim_entries if claim["status"] == "partial")
    unsupported_count = sum(1 for claim in claim_entries if claim["status"] == "unsupported")
    total_claims = len(claim_entries)

    source_count = len(source_nodes) if source_nodes else len(visited_urls)
    support_rate = round(supported_count / total_claims, 3) if total_claims else 1.0
    unsupported_ratio = round(unsupported_count / total_claims, 3) if total_claims else 0.0

    risk = classify_risk(query, report_markdown, [claim["claim"] for claim in claim_entries])
    if risk["level"] == "high" or unsupported_ratio >= 0.5:
        risk["human_review_required"] = True

    summary = {
        "claims_total": total_claims,
        "supported_claims": supported_count,
        "partial_claims": partial_count,
        "unsupported_claims": unsupported_count,
        "support_rate": support_rate,
        "unsupported_ratio": unsupported_ratio,
        "source_count": source_count,
        "evidence_edges": len(evidence_edges),
    }

    return {
        "query": query,
        "risk": risk,
        "summary": summary,
        "claims": claim_entries,
        "evidence_graph": {
            "nodes": evidence_nodes,
            "edges": evidence_edges,
        },
    }


def render_verification_section(bundle: dict[str, Any]) -> str:
    """Render a human-readable verification appendix."""
    summary = bundle.get("summary", {})
    risk = bundle.get("risk", {})
    claims = bundle.get("claims", [])
    lines: list[str] = [
        "## Verification Review",
        f"- Risk level: {risk.get('level', 'unknown')}",
        f"- Human review required: {'yes' if risk.get('human_review_required') else 'no'}",
        f"- Claims analyzed: {summary.get('claims_total', 0)}",
        f"- Supported claims: {summary.get('supported_claims', 0)}",
        f"- Partial claims: {summary.get('partial_claims', 0)}",
        f"- Unsupported claims: {summary.get('unsupported_claims', 0)}",
        f"- Support rate: {summary.get('support_rate', 0.0):.0%}",
        f"- Source coverage: {summary.get('source_count', 0)}",
    ]

    reason = risk.get("reason")
    if reason:
        lines.append(f"- Risk reason: {reason}")

    if not claims:
        lines.extend(
            [
                "",
                "### Claim Ledger",
                "- No verifiable claims could be extracted from the report body.",
            ]
        )
        return "\n".join(lines).strip()

    lines.extend(["", "### Claim Ledger"])
    for claim in claims[:12]:
        status = claim.get("status", "unknown")
        sources = claim.get("sources", [])
        source_labels = []
        for source in sources[:3]:
            source_url = source.get("source_url")
            if source_url:
                source_labels.append(f"[{source_url}]({source_url})")
            else:
                source_labels.append(source.get("source_id", "unknown source"))

        if source_labels:
            sources_text = ", ".join(source_labels)
        else:
            sources_text = "no direct context match"

        lines.append(
            f"- {status.upper()}: {claim.get('claim')}  "
            f"(confidence {claim.get('confidence', 0.0):.2f}; sources: {sources_text})"
        )

    lines.extend(
        [
            "",
            "### Evidence Graph Summary",
            f"- Nodes: {len(bundle.get('evidence_graph', {}).get('nodes', []))}",
            f"- Edges: {len(bundle.get('evidence_graph', {}).get('edges', []))}",
        ]
    )

    if risk.get("human_review_required"):
        lines.extend(
            [
                "",
                "### Human Review Note",
                "- This topic should be reviewed manually before relying on the conclusions.",
            ]
        )

    return "\n".join(lines).strip()
