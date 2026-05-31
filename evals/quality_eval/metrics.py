"""
Quality Evaluation Metrics
--------------------------
All report quality metrics in one module.

Zero-cost metrics (no LLM calls):
  citation_ratio()    — fraction of used source domains cited in the report
  source_diversity()  — domain variety via ratio + Shannon entropy
  source_authority()  — heuristic authority score; unknown domains use LLM if provided

LLM metrics (~$0.02/query each):
  subtopic_coverage() — how thoroughly the report covers expected subtopics
  unsupported_claim() — claim-level credibility scoring (supported / inferred / unsupported)
"""

import json
import math
import re
from collections import Counter
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _extract_domains(urls: list[str]) -> set[str]:
    """Return normalised domain set from a list of URLs (strips www.)."""
    return {urlparse(u).netloc.lower().lstrip("www.") for u in urls if u}


def _extract_domains_from_text(text: str) -> set[str]:
    """Scan raw text for URLs and extract their domains."""
    urls = re.findall(r'https?://[^\s\)\]\,\"\'<>]+', text)
    return _extract_domains(urls)


def _parse_json(text: str):
    """Parse JSON from an LLM response, tolerating markdown code fences."""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
    if match:
        text = match.group(1)
    return json.loads(text)


# ---------------------------------------------------------------------------
# 1. Citation Ratio
# ---------------------------------------------------------------------------

def citation_ratio(report: str, source_urls: list[str], context=None) -> dict:
    """
    Fraction of used source domains that are explicitly cited in the report.

    Args:
        report:      Full markdown report text.
        source_urls: URLs from researcher.get_source_urls().
        context:     Raw context from researcher.conduct_research() (str or list).
                     When provided, denominator = domains that made it into context
                     (relevance-filtered), giving a fairer ratio than all visited sources.

    NOTE: Low ratio does not necessarily mean poor reporting — the researcher may
    have legitimately discarded irrelevant sources after reading them.
    TODO (Phase 3): weight denominator by embedding similarity to further refine.
    """
    if not source_urls:
        return {
            "total_source_domains": 0,
            "used_source_domains":  0,
            "cited_source_count":   0,
            "citation_presence":    False,
            "citation_ratio":       0.0,
            "uncited_domains":      [],
        }

    source_domains = _extract_domains(source_urls)

    if context:
        context_text = context if isinstance(context, str) else json.dumps(context)
        used_domains = _extract_domains_from_text(context_text) & source_domains
    else:
        used_domains = source_domains

    cited_domains = _extract_domains_from_text(report)
    covered = cited_domains & used_domains
    denom   = len(used_domains) if used_domains else len(source_domains)

    return {
        "total_source_domains": len(source_domains),
        "used_source_domains":  len(used_domains),
        "cited_source_count":   len(covered),
        "citation_presence":    len(covered) > 0,
        "citation_ratio":       round(len(covered) / denom, 3) if denom else 0.0,
        "uncited_domains":      sorted(used_domains - cited_domains),
    }


# ---------------------------------------------------------------------------
# 2. Source Diversity
# ---------------------------------------------------------------------------

def source_diversity(source_urls: list[str]) -> dict:
    """
    Domain variety measured by ratio and Shannon entropy.

    diversity_ratio = unique domains / total sources  (0–1)
    domain_entropy  = Shannon entropy over domain distribution
                      (higher = more evenly spread, no single domain dominates)
    """
    if not source_urls:
        return {
            "total_sources":   0,
            "unique_domains":  0,
            "diversity_ratio": 0.0,
            "domain_entropy":  0.0,
            "top_domains":     [],
        }

    domains = [urlparse(u).netloc.lower().lstrip("www.") for u in source_urls if u]
    counts  = Counter(domains)
    total   = len(domains)
    unique  = len(counts)

    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())

    # diversity_ratio = unique_domains / total_sources
    # Shannon Entropy = -sum((c/total) * log2(c/total) for c in counts.values())
    return {
        "total_sources":   total,
        "unique_domains":  unique,
        "diversity_ratio": round(unique / total, 3),
        "domain_entropy":  round(entropy, 3),
        "top_domains":     counts.most_common(3),
    }


# ---------------------------------------------------------------------------
# 3. Source Authority
# ---------------------------------------------------------------------------

_HIGH_AUTHORITY_DOMAINS = {
    "nature.com", "science.org", "cell.com", "thelancet.com",
    "nejm.org", "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
    "arxiv.org", "scholar.google.com", "jstor.org", "ssrn.com",
    "plos.org", "biorxiv.org", "medrxiv.org",
    "who.int", "un.org", "imf.org", "worldbank.org",
    "oecd.org", "wto.org", "europa.eu",
    "britannica.com",
}

_MAJOR_NEWS_DOMAINS = {
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com",
    "nytimes.com", "theguardian.com", "washingtonpost.com",
    "wsj.com", "economist.com", "ft.com", "bloomberg.com",
    "npr.org", "pbs.org", "aljazeera.com",
}

_LLM_AUTHORITY_PROMPT = """
You are a research source evaluator.

Rate the authority of each domain below as a research source on a scale of 0.0 to 1.0.
Consider whether it is a known academic journal, government body, established news outlet,
professional organization, or specialized expert source.

Domains:
{domains}

Return ONLY a JSON array in this exact format, one entry per domain:
[{{"domain": "example.com", "score": 0.7, "reason": "established tech news outlet"}}]
""".strip()


def _score_domain(domain: str) -> tuple[float, str]:
    # TODO (Phase 3): Hybrid authority scoring — batch LLM call for unknown domains.
    # Current rule table defaults unknown domains to 0.4 regardless of actual authority.
    d = domain.lower().lstrip("www.")
    if d.endswith(".gov"):           return 1.0, "government"
    if d.endswith(".edu"):           return 0.9, "academic-edu"
    if d in _HIGH_AUTHORITY_DOMAINS: return 0.9, "high-authority"
    if d in _MAJOR_NEWS_DOMAINS:     return 0.8, "major-news"
    if "wikipedia.org" in d:         return 0.75, "wikipedia"
    if d.endswith(".org"):           return 0.65, "nonprofit-org"
    if d.endswith(".com"):           return 0.5,  "commercial"
    return 0.4, "unknown"


async def _llm_score_domains(domains: list[str], grader_model) -> list[dict]:
    prompt = _LLM_AUTHORITY_PROMPT.format(
        domains="\n".join(f"- {d}" for d in domains)
    )
    try:
        resp    = await grader_model.ainvoke(prompt)
        results = _parse_json(resp.content)
        return [
            {"domain": r["domain"], "score": float(r["score"]), "tier": f"llm:{r.get('reason','')}"}
            for r in results
        ]
    except Exception:
        return [{"domain": d, "score": 0.4, "tier": "unknown"} for d in domains]


async def source_authority(source_urls: list[str], grader_model=None) -> dict:
    """
    Average authority score per source domain (0.0–1.0).

    Rule-based tiers: .gov=1.0, .edu=0.9, known academic/news=0.8-0.9,
    wikipedia=0.75, .org=0.65, .com=0.5, unknown=0.4.
    When grader_model is provided, unknown domains are batch-scored by LLM.
    """
    if not source_urls:
        return {"avg_authority_score": 0.0, "breakdown": []}

    known, unknown_domains = [], []

    for url in source_urls:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        score, tier = _score_domain(domain)
        if tier == "unknown" and grader_model:
            unknown_domains.append(domain)
        else:
            known.append({"domain": domain, "score": score, "tier": tier})

    llm_scores = []
    if unknown_domains and grader_model:
        llm_scores = await _llm_score_domains(unknown_domains, grader_model)
    elif unknown_domains:
        llm_scores = [{"domain": d, "score": 0.4, "tier": "unknown"} for d in unknown_domains]

    breakdown = known + llm_scores
    avg = sum(b["score"] for b in breakdown) / len(breakdown)

    return {
        "avg_authority_score": round(avg, 3),
        "breakdown": sorted(breakdown, key=lambda x: -x["score"]),
    }


# ---------------------------------------------------------------------------
# 4. Subtopic Coverage
# ---------------------------------------------------------------------------

_SUBTOPICS_PROMPT = """
You are a research quality evaluator.

List the key subtopics that a comprehensive research report on the following
question must cover to be considered thorough.

Guidelines for choosing how many subtopics to list:
- Narrow or specific questions (e.g. a single fact, date, or person): 2-3 subtopics
- Moderate questions (e.g. a process, event, or comparison): 4-5 subtopics
- Broad or complex questions (e.g. a trend, field, or multi-factor topic): 6-7 subtopics

Return ONLY a JSON array of short subtopic strings (3-6 words each).
Do not include any explanation or extra text.

Question: {query}
""".strip()

_COVERAGE_PROMPT = """
You are a research quality evaluator.

Given the list of expected subtopics and the research report excerpt below,
identify which subtopics are clearly addressed and which are missing or
only superficially mentioned.

Expected subtopics:
{subtopics}

Report (first 3000 characters):
{report}

Return ONLY a JSON object in this exact format:
{{"covered": ["subtopic1", ...], "missing": ["subtopic2", ...]}}
""".strip()


async def subtopic_coverage(query: str, report: str, grader_model) -> dict:
    """
    LLM-judged coverage of expected subtopics (~2 calls, ~$0.02/query).

    Step 1: generate expected subtopics for the query (adaptive count).
    Step 2: check which subtopics the report covers.
    """
    try:
        resp1     = await grader_model.ainvoke(_SUBTOPICS_PROMPT.format(query=query))
        subtopics = _parse_json(resp1.content)
    except Exception:
        return {
            "expected_subtopics":     [],
            "covered":                [],
            "missing":                [],
            "subtopic_coverage_rate": None,
            "error":                  "Failed to parse subtopics from LLM",
        }

    try:
        resp2  = await grader_model.ainvoke(
            _COVERAGE_PROMPT.format(
                subtopics=json.dumps(subtopics, ensure_ascii=False),
                report=report[:3000],
            )
        )
        result  = _parse_json(resp2.content)
        covered = result.get("covered", [])
        missing = result.get("missing", [])
    except Exception:
        return {
            "expected_subtopics":     subtopics,
            "covered":                [],
            "missing":                subtopics,
            "subtopic_coverage_rate": None,
            "error":                  "Failed to parse coverage from LLM",
        }

    total = len(subtopics)
    return {
        "expected_subtopics":     subtopics,
        "covered":                covered,
        "missing":                missing,
        "subtopic_coverage_rate": round(len(covered) / total, 3) if total else 0.0,
    }


# ---------------------------------------------------------------------------
# 5. Unsupported Claim Rate
# ---------------------------------------------------------------------------

_EXTRACT_CLAIMS_PROMPT = """
You are a fact-checking assistant.

Extract specific, verifiable factual claims from the research report below.
Focus on concrete statements: dates, numbers, names, causal relationships, statistics.
Exclude: opinions, vague generalisations, hedged statements, and section summaries.

Guidelines for how many claims to extract:
- Short or narrow reports: 3-5 claims
- Typical research reports: 6-8 claims
- Long or multi-topic reports: up to 10 claims

Report (first 3000 characters):
{report}

Return ONLY a JSON array of claim strings. No explanation or extra text.
""".strip()

_VERIFY_CLAIMS_PROMPT = """
You are a fact-checking assistant.

For each claim below, assign a credibility score (0.0–1.0) based on
how well the source context supports it.

Scoring rules:

score = 1.0  →  "supported"
  The context directly and explicitly states the claim.
  This is the ONLY valid score for claims containing specific data:
  numbers, percentages, dates, statistics, version numbers, or named figures.

score = 0.3–0.9  →  "inferred"
  The claim is a reasonable synthesis drawn from multiple parts of the context,
  but no single source states it explicitly.
  Only applicable to conceptual or summary statements — NEVER to data claims.
  Score higher when more authoritative sources (3+) support the inference (→ 0.75–0.9).
  Score lower when only 1–2 commercial sources loosely imply it (→ 0.3–0.5).

score = 0.0  →  "unsupported"
  No traceable basis in context, contradicted, or specific data not found in context.

Important: do not use your own knowledge — only use the provided context.
Any claim with a specific number, date, or statistic not in the context → score 0.0.

Claims:
{claims}

Source context (first 4000 characters):
{context}

Return ONLY a JSON array, one object per claim:
[
  {{"claim": "...", "category": "supported",   "score": 1.0,  "reason": "..."}},
  {{"claim": "...", "category": "inferred",    "score": 0.75, "reason": "..."}},
  {{"claim": "...", "category": "unsupported", "score": 0.0,  "reason": "..."}}
]
""".strip()


async def unsupported_claim(report: str, context, grader_model) -> dict:
    """
    Claim-level credibility scoring (~2 calls, ~$0.02/query).

    Step 1: extract 3-10 specific verifiable claims from the report.
    Step 2: score each claim as supported (1.0), inferred (0.3-0.9), or unsupported (0.0).

    Data claims (numbers/dates/stats) are strictly supported or unsupported — never inferred.
    Returns avg_claim_score (overall credibility), unsupported_claim_rate (hard failures only),
    inferred_claim_rate (synthesis proportion), and per-claim breakdown.
    """
    context_text = context if isinstance(context, str) else json.dumps(context)

    try:
        resp1  = await grader_model.ainvoke(_EXTRACT_CLAIMS_PROMPT.format(report=report[:3000]))
        claims = _parse_json(resp1.content)
    except Exception as e:
        return {
            "total_claims": 0, "avg_claim_score": None,
            "unsupported_claim_rate": None, "inferred_claim_rate": None,
            "breakdown": [], "error": f"Claim extraction failed: {e}",
        }

    if not claims:
        return {
            "total_claims": 0, "avg_claim_score": 0.0,
            "unsupported_claim_rate": 0.0, "inferred_claim_rate": 0.0,
            "breakdown": [],
        }

    try:
        resp2         = await grader_model.ainvoke(
            _VERIFY_CLAIMS_PROMPT.format(
                claims=json.dumps(claims, ensure_ascii=False),
                context=context_text[:4000],
            )
        )
        scored_claims = _parse_json(resp2.content)
    except Exception as e:
        return {
            "total_claims": len(claims), "avg_claim_score": None,
            "unsupported_claim_rate": None, "inferred_claim_rate": None,
            "breakdown": [], "error": f"Claim verification failed: {e}",
        }

    supported_l   = [c for c in scored_claims if c.get("category") == "supported"]
    inferred_l    = [c for c in scored_claims if c.get("category") == "inferred"]
    unsupported_l = [c for c in scored_claims if c.get("category") == "unsupported"]

    total     = len(scored_claims)
    avg_score = round(sum(float(c.get("score", 0.0)) for c in scored_claims) / total, 3) if total else 0.0

    return {
        "total_claims":           total,
        "supported_count":        len(supported_l),
        "inferred_count":         len(inferred_l),
        "unsupported_count":      len(unsupported_l),
        "avg_claim_score":        avg_score,
        "unsupported_claim_rate": round(len(unsupported_l) / total, 3) if total else 0.0,
        "inferred_claim_rate":    round(len(inferred_l)    / total, 3) if total else 0.0,
        "breakdown": [
            {
                "claim":    c.get("claim"),
                "category": c.get("category"),
                "score":    float(c.get("score", 0.0)),
                "reason":   c.get("reason", ""),
            }
            for c in scored_claims
        ],
    }
