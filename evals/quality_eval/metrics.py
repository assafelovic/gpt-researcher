"""
Quality Evaluation Metrics
--------------------------
All report quality metrics in one module, grouped by what they measure:

Source Quality — is the input good?
  source_diversity()      — domain variety via ratio + Shannon entropy        ($0)
  source_authority()      — authority score; unknown domains use LLM if given  ($0 / LLM)

Writing Behavior — how was the report written?
  citation_faithfulness() — do cited-in-body sources match the References list ($0)
  subtopic_coverage()     — how thoroughly the report covers expected subtopics (LLM)

Hallucination — is the content supported?
  unsupported_claim()     — claim-level credibility (supported/inferred/unsupported) (LLM)
"""

import asyncio
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
    return {urlparse(u).netloc.lower().removeprefix("www.") for u in urls if u}


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


def _split_at_references(report: str) -> tuple[str, str]:
    """Split a report into (body, references_section).

    Both single- and multi-agent reports end with a `## References` (or
    Sources/Citations/Bibliography) section listing every source. That list is
    not evidence the body was written from those sources, so citation metrics
    should look at the body only. Returns (body, refs); refs is "" if absent.
    """
    m = re.search(r'(?im)^#+\s*(references|sources|citations|bibliography)\s*$', report)
    if m:
        return report[:m.start()], report[m.start():]
    return report, ""


# ---------------------------------------------------------------------------
# 1. Citation Faithfulness  (Writing Behavior)
# ---------------------------------------------------------------------------

def citation_faithfulness(report: str, source_urls: list[str], context=None) -> dict:
    """
    Alignment between the sources a report CLAIMS to use and the sources it
    actually cites in the prose.

        citation_faithfulness = |cited_in_body ∩ listed_in_refs| / |listed_in_refs|

      1.0  = every source in the trailing `## References` list is actually
             referenced somewhere in the body
      low  = many sources are listed as references but never cited in the prose
             (decorative / unused citations — a self-consistency failure)
      None = the report has no References section to compare against

    This measures the LLM's citation discipline (does it use what it claims to
    use?), NOT whether the content is correct — that is unsupported_claim's job.

    Also returns `citation_coverage` as a DESCRIPTIVE statistic (not a quality
    score): of the sources actually used in research, how many are cited in the
    body. A low coverage can simply mean the agent sensibly discarded sources,
    so it should not be read as a quality signal on its own.

    Args:
        report:      Full markdown report text.
        source_urls: URLs from researcher.get_source_urls().
        context:     Raw context from researcher.conduct_research() (str or list);
                     when provided, coverage denominator = sources that made it
                     into context (relevance-filtered).
    """
    source_domains = _extract_domains(source_urls)

    body, refs     = _split_at_references(report)
    cited_domains  = _extract_domains_from_text(body)   # in-text citations only
    listed_domains = _extract_domains_from_text(refs)   # end-of-report list only

    # --- Faithfulness: of what is listed as references, how much is cited in body ---
    if listed_domains:
        aligned      = cited_domains & listed_domains
        faithfulness = round(len(aligned) / len(listed_domains), 3)
        listed_only  = sorted(listed_domains - cited_domains)
    else:
        faithfulness = None        # no references section → not applicable
        listed_only  = []

    # --- Coverage (descriptive only) ---
    if context:
        context_text = context if isinstance(context, str) else json.dumps(context)
        used_domains = _extract_domains_from_text(context_text) & source_domains
    else:
        used_domains = source_domains
    covered  = cited_domains & used_domains
    coverage = round(len(covered) / len(used_domains), 3) if used_domains else None

    return {
        "citation_faithfulness": faithfulness,
        "listed_ref_domains":    len(listed_domains),
        "cited_body_domains":    len(cited_domains),
        "listed_only_domains":   listed_only,    # listed as ref but never cited in body
        "citation_coverage":     coverage,       # descriptive, NOT a quality score
        "uncited_used_domains":  sorted(used_domains - cited_domains),
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

    domains = [urlparse(u).netloc.lower().removeprefix("www.") for u in source_urls if u]
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


def _score_domain(domain: str):
    """High-confidence rule match only.

    Returns (score, tier) for domains we can score reliably by rule
    (.gov, .edu, known academic/news whitelists, wikipedia), or None to
    signal the domain should be deferred to the LLM.

    NOTE: .com / .org are intentionally NOT scored here. Many high-authority
    sources live on .com/.org (e.g. sciencedirect.com, bmj.com, cureus.com),
    so a blanket ".com → 0.5" rule misclassifies them as low-authority and,
    critically, prevents them from ever reaching the LLM scorer. We defer all
    such domains to the LLM instead (batched, so cost stays at ~1 call/query).
    """
    d = domain.lower().removeprefix("www.")
    if d.endswith(".gov"):           return 1.0, "government"
    if d.endswith(".edu"):           return 0.9, "academic-edu"
    if d in _HIGH_AUTHORITY_DOMAINS: return 0.9, "high-authority"
    if d in _MAJOR_NEWS_DOMAINS:     return 0.8, "major-news"
    if "wikipedia.org" in d:         return 0.75, "wikipedia"
    return None   # defer .com / .org / everything else to the LLM


def _fallback_score(domain: str) -> tuple[float, str]:
    """Rule-only score for deferred domains when no grader_model is available."""
    d = domain.lower().removeprefix("www.")
    if d.endswith(".org"): return 0.65, "nonprofit-org"
    if d.endswith(".com"): return 0.5,  "commercial"
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

    High-confidence rule tiers: .gov=1.0, .edu=0.9, known academic/news=0.8-0.9,
    wikipedia=0.75. Everything else (.com, .org, unknown TLDs) is deferred to a
    single batched LLM call when grader_model is provided — this is what lets
    sources like sciencedirect.com or bmj.com be recognised as high-authority.
    Without a grader_model, deferred domains fall back to .org=0.65 / .com=0.5 / 0.4.
    """
    if not source_urls:
        return {"avg_authority_score": 0.0, "breakdown": []}

    domains = [urlparse(u).netloc.lower().removeprefix("www.") for u in source_urls if u]

    breakdown = []
    deferred  = []
    for domain in domains:
        match = _score_domain(domain)
        if match is not None:
            score, tier = match
            breakdown.append({"domain": domain, "score": score, "tier": tier})
        else:
            deferred.append(domain)

    if deferred:
        score_map = {}
        if grader_model:
            # Batch-score unique deferred domains in a single LLM call.
            scored    = await _llm_score_domains(sorted(set(deferred)), grader_model)
            score_map = {s["domain"]: s for s in scored}
        for domain in deferred:
            entry = score_map.get(domain)
            if entry is None:
                fb_score, fb_tier = _fallback_score(domain)
                entry = {"domain": domain, "score": fb_score, "tier": fb_tier}
            breakdown.append(dict(entry))

    if not breakdown:
        return {"avg_authority_score": 0.0, "breakdown": []}

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

_COVERAGE_ONE_PROMPT = """
You are a research quality evaluator.

Decide whether the single subtopic below is clearly and substantively addressed
in the research report (not merely mentioned in passing).

Subtopic: {subtopic}

Report:
{report}

Return ONLY a JSON object: {{"covered": true}} or {{"covered": false}}.
""".strip()


async def _check_one_subtopic(subtopic: str, report: str, grader_model) -> bool:
    """Judge a single subtopic's coverage independently (no batch effects)."""
    try:
        resp   = await grader_model.ainvoke(
            _COVERAGE_ONE_PROMPT.format(subtopic=subtopic, report=report[:12000]))
        result = _parse_json(resp.content)
        return bool(result.get("covered", False))
    except Exception:
        return False


async def subtopic_coverage(query: str, report: str, grader_model, subtopics=None) -> dict:
    """
    LLM-judged coverage of expected subtopics (~2 calls, ~$0.02/query).

    Step 1: generate expected subtopics for the query (adaptive count).
    Step 2: check which subtopics the report covers.

    `subtopics`: optional pre-generated subtopic list. When provided, step 1 is
    skipped and coverage is judged against these exact subtopics — this fixes the
    subtopic set across calls (e.g. for perturbation testing, so coverage isn't
    confounded by re-generation drift).
    """
    if subtopics is None:
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

    # Judge each subtopic INDEPENDENTLY (one call each, concurrent) so a
    # subtopic's verdict isn't swayed by the others in the same batch.
    flags   = await asyncio.gather(
        *(_check_one_subtopic(s, report, grader_model) for s in subtopics)
    )
    covered = [s for s, ok in zip(subtopics, flags) if ok]
    missing = [s for s, ok in zip(subtopics, flags) if not ok]

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


async def _verify_one_claim(claim: str, context_text: str, grader_model) -> dict:
    """Score a single claim independently against the context (no batch effects)."""
    try:
        resp   = await grader_model.ainvoke(
            _VERIFY_CLAIMS_PROMPT.format(
                claims=json.dumps([claim], ensure_ascii=False),
                context=context_text[:4000],
            )
        )
        result = _parse_json(resp.content)
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    return {"claim": claim, "category": "unsupported", "score": 0.0,
            "reason": "verification failed"}


async def unsupported_claim(report: str, context, grader_model, claims=None) -> dict:
    """
    Claim-level credibility scoring (~2 calls, ~$0.02/query).

    Step 1: extract 3-10 specific verifiable claims from the report.
    Step 2: score each claim as supported (1.0), inferred (0.3-0.9), or unsupported (0.0).

    Data claims (numbers/dates/stats) are strictly supported or unsupported — never inferred.
    Returns avg_claim_score (overall credibility), unsupported_claim_rate (hard failures only),
    inferred_claim_rate (synthesis proportion), and per-claim breakdown.

    `claims`: optional pre-extracted claim list. When provided, the extraction
    step is skipped and these exact claims are scored — this fixes the claim set
    across calls (e.g. for perturbation testing, so scoring isn't confounded by
    re-extraction drift).
    """
    context_text = context if isinstance(context, str) else json.dumps(context)

    if claims is None:
        try:
            resp1  = await grader_model.ainvoke(_EXTRACT_CLAIMS_PROMPT.format(report=report[:12000]))
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

    # Score each claim INDEPENDENTLY (one LLM call per claim, run concurrently).
    # Batch scoring let a corrupted/absurd claim shift the model's judgement of
    # unrelated claims in the same batch — so a claim's score depended on its
    # batch-mates. Independent scoring makes each claim's score self-contained.
    scored_claims = await asyncio.gather(
        *(_verify_one_claim(c, context_text, grader_model) for c in claims)
    )

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


# ---------------------------------------------------------------------------
# Orchestration  (shared by run_eval.py and benchmark.py)
# ---------------------------------------------------------------------------

def skipped(reason: str) -> dict:
    """Sentinel returned when a metric can't run, so one failure doesn't abort."""
    return {"status": "skipped", "reason": reason}


def is_skipped(value) -> bool:
    return isinstance(value, dict) and value.get("status") == "skipped"


async def _safe(coro, name: str):
    """Await a metric coroutine; on any exception return a skipped sentinel."""
    try:
        return await coro
    except Exception as e:
        print(f"   [WARN] {name} failed: {type(e).__name__}: {e}")
        return skipped(f"{type(e).__name__}: {e}")


async def evaluate_report(
    report: str,
    sources: list,
    context,
    query: str,
    grader_model,
    *,
    run_subtopic: bool = True,
    run_unsupported: bool = True,
) -> dict:
    """Compute all quality metrics for one report.

    Each metric is wrapped so a failure becomes a `skipped()` sentinel rather
    than aborting the whole evaluation. Returns a dict keyed by metric name;
    callers add latency/cost/console output and any extra metrics (e.g.
    run_eval's hallucination check). Zero-cost metrics always run; the two LLM
    metrics are gated by the flags.
    """
    out = {}

    try:
        out["citation_faithfulness"] = citation_faithfulness(report, sources, context=context)
    except Exception as e:
        out["citation_faithfulness"] = skipped(str(e))

    try:
        out["source_diversity"] = source_diversity(sources)
    except Exception as e:
        out["source_diversity"] = skipped(str(e))

    out["source_authority"] = await _safe(
        source_authority(sources, grader_model=grader_model), "source_authority"
    )

    out["subtopic_coverage"] = (
        await _safe(subtopic_coverage(query, report, grader_model), "subtopic_coverage")
        if run_subtopic else None
    )

    if run_unsupported:
        out["unsupported_claim"] = (
            skipped("no source context available") if not context
            else await _safe(unsupported_claim(report, context, grader_model), "unsupported_claim")
        )
    else:
        out["unsupported_claim"] = None

    return out
