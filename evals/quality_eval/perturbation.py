"""
Perturbation (behavioral) test for quality_eval metrics.
--------------------------------------------------------
Validates metric RELIABILITY: when a report or its sources are deliberately
degraded, does the matching metric move in the expected direction — and
monotonically as the degradation grows? This catches implementation bugs that
pure logic cannot. For example, if `_split_at_references` were broken,
citation_faithfulness would stay high even after every inline citation is
removed; this test would catch that.

IMPORTANT — reliability vs validity:
  This test only proves the metrics are implemented correctly and are
  directionally sensitive (reliability). It does NOT prove they measure
  "report quality" (validity). Notably, claim_score is known to reward
  extractive (copy-from-source) over abstractive (synthesis) writing — a
  separate validity concern that perturbation cannot address.

Runs over multiple real gpt-4o reports (fixtures) so a result is a consistent
property of the metric, not an artifact of one report.

Usage:
    python -m evals.quality_eval.perturbation
"""

import asyncio
import json
import os
import random
import re
import sys
from pathlib import Path

from evals.quality_eval import metrics

FIXTURES  = Path(__file__).parent / "fixtures" / "perturbation_fixtures.json"
FRACTIONS = [0.0, 0.25, 0.50, 0.75, 1.0]

# Low-authority replacement URLs used to degrade source_authority.
_LOW_AUTHORITY = [
    "https://medium.com/@user/post-{}",
    "https://www.reddit.com/r/topic/comments/{}",
    "https://someblog.blogspot.com/{}",
]

# Polarity flips used to corrupt factual claims (_corrupt_text).
_POLARITY = {
    "increase": "decrease", "increases": "decreases", "increased": "decreased",
    "decrease": "increase", "decreases": "increases", "decreased": "increased",
    "effective": "ineffective", "ineffective": "effective",
    "higher": "lower", "lower": "higher", "more": "less", "less": "more",
    "positive": "negative", "negative": "positive",
    "improve": "worsen", "improves": "worsens", "improved": "worsened",
    "reduce": "raise", "reduces": "raises", "reduced": "raised",
    "significant": "negligible", "significantly": "negligibly",
}

# Stopwords skipped when picking "key" content words to corrupt.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "of", "to",
    "in", "and", "or", "for", "with", "on", "at", "by", "as", "that", "this", "it",
    "its", "from", "which", "their", "they", "these", "those", "has", "have", "had",
    "not", "but", "can", "may", "will", "such", "also", "than", "when", "while",
}

# Fixed decoy words used to replace key entities (deterministic given the seed).
_DECOY_WORDS = [
    "wombat", "teapot", "bicycle", "umbrella", "marshmallow", "saxophone",
    "tundra", "pelican", "concrete", "lullaby", "thermostat", "origami",
]


# ---------------------------------------------------------------------------
# Perturbation functions — each degrades ONE input dimension by `fraction`
# ---------------------------------------------------------------------------

def degrade_citations(report: str, fraction: float) -> str:
    """Remove `fraction` of inline [text](url) links from the BODY only.

    The trailing `## References` list is preserved, and each removed link is
    replaced by its anchor text so the prose stays readable. Expected effect:
    citation_faithfulness drops (sources stay listed in References but are no
    longer cited in the body).
    """
    body, refs = metrics._split_at_references(report)
    links = list(re.finditer(r'\[([^\]]+)\]\((https?://[^\)]+)\)', body))
    n = round(len(links) * fraction)
    # Remove the last n links back-to-front so earlier offsets stay valid.
    for m in sorted(links[len(links) - n:], key=lambda x: -x.start()):
        body = body[:m.start()] + m.group(1) + body[m.end():]
    return body + refs


def degrade_authority(sources: list[str], fraction: float) -> list[str]:
    """Replace `fraction` of sources with low-authority blog/forum URLs.

    Expected effect: avg_authority_score drops as authoritative domains
    (.gov / journals) are swapped for blogs and forums.
    """
    out = list(sources)
    n = round(len(out) * fraction)
    for i in range(n):
        out[i] = _LOW_AUTHORITY[i % len(_LOW_AUTHORITY)].format(i)
    return out


def degrade_diversity(sources: list[str], fraction: float) -> list[str]:
    """Collapse `fraction` of sources onto a single shared domain.

    Expected effect: diversity_ratio drops toward 1/N as distinct domains are
    replaced by paths on one domain.
    """
    out = list(sources)
    n = round(len(out) * fraction)
    for i in range(n):
        out[i] = f"https://onedomain.com/page{i}"
    return out


def degrade_subtopics(report: str, fraction: float) -> str:
    """Remove the last `fraction` of the report's sections (## headers).

    The body is split on `## ` headers; the trailing `fraction` of sections is
    dropped (intro and References kept). Expected effect: subtopic_coverage
    drops as whole sections — and the subtopics they cover — disappear.
    """
    body, refs = metrics._split_at_references(report)
    parts = re.split(r'(?=^##\s)', body, flags=re.M)   # keep each header with its content
    n_drop = round(len(parts) * fraction)
    kept = parts[:len(parts) - n_drop] if n_drop else parts
    return "".join(kept) + ("\n\n" + refs if refs else "")


def _corrupt_text(text: str, rng: random.Random) -> str:
    """Deterministically corrupt a claim so it contradicts the context.

    Three rule-based, reproducible operations (given the seed):
      1. flip polarity words (increase<->decrease, effective<->ineffective, ...)
      2. swap every number for a different random number
      3. replace the two longest content words (likely key entities/nouns) with
         fixed decoy words — this is what lets QUALITATIVE claims (e.g. legal
         definitions, with no numbers) be corrupted at all.
    """
    def _flip(m):
        w = m.group()
        new = _POLARITY[w.lower()]
        return new.capitalize() if w[:1].isupper() else new
    text = re.sub(r'\b(' + '|'.join(_POLARITY) + r')\b', _flip, text, flags=re.I)
    text = re.sub(r'\b\d+(?:\.\d+)?(%?)\b',
                  lambda m: str(rng.randint(1, 99)) + m.group(1), text)

    # Key-entity corruption: replace the 2 longest content words with decoys.
    words = text.split()
    ranked = sorted(
        (i for i, w in enumerate(words)
         if w.strip(".,;:()").lower() not in _STOPWORDS and len(w.strip(".,;:()")) > 3),
        key=lambda i: -len(words[i]),
    )
    for i in ranked[:2]:
        words[i] = rng.choice(_DECOY_WORDS)
    return " ".join(words)


def corrupt_claims(claims: list[str], fraction: float, seed: int = 0) -> list[str]:
    """Corrupt `fraction` of a FIXED claim set (numbers + polarity flips) so the
    corrupted ones contradict the context.

    Key difference from corrupting the report: the claim set is extracted ONCE and
    held constant; only a growing subset is corrupted. This removes the
    re-extraction drift that made the report-level perturbation noisy. Expected
    effect: unsupported_claim_rate RISES monotonically with `fraction`.
    """
    rng = random.Random(seed)
    # Fixed shuffle so corrupted subsets are NESTED across fractions
    # (25% corrupted ⊂ 50% corrupted ⊂ ...); otherwise monotonicity is spurious.
    order = list(range(len(claims)))
    rng.shuffle(order)
    n = round(len(claims) * fraction)
    corrupt_idx = set(order[:n])
    return [_corrupt_text(c, rng) if i in corrupt_idx else c
            for i, c in enumerate(claims)]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _monotone(vals, increasing: bool = False) -> bool:
    clean = [v for v in vals if v is not None]
    if increasing:
        return all(a <= b + 1e-9 for a, b in zip(clean, clean[1:]))
    return all(a >= b - 1e-9 for a, b in zip(clean, clean[1:]))


def _row(topic: str, vals, increasing: bool = False) -> str:
    cells = "".join(f"{v:>8.2f}" if v is not None else f"{'--':>8}" for v in vals)
    verdict = "PASS" if _monotone(vals, increasing) else "FAIL  <-- not monotone!"
    return f"  {topic:<10}{cells}   {verdict}"


def _header() -> str:
    return f"  {'topic':<10}" + "".join(f"{int(f*100):>7}%" for f in FRACTIONS) + "   monotone?"


async def main():
    if not FIXTURES.exists():
        raise SystemExit(f"Fixtures not found: {FIXTURES}\nGenerate them first (3 gpt-4o reports).")
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    print(f"Loaded {len(fixtures)} fixtures: {[f['topic'] for f in fixtures]}\n")

    # --- citation_faithfulness: remove inline body citations (zero-cost) ---
    print("=== citation_faithfulness  (remove inline body citations) ===")
    print(_header())
    for fx in fixtures:
        vals = [
            metrics.citation_faithfulness(
                degrade_citations(fx["report"], f), fx["sources"], context=fx["context"]
            )["citation_faithfulness"]
            for f in FRACTIONS
        ]
        print(_row(fx["topic"], vals))

    # --- source_diversity: collapse domains (zero-cost) ---
    print("\n=== source_diversity  (collapse onto one domain) ===")
    print(_header())
    for fx in fixtures:
        vals = [
            metrics.source_diversity(degrade_diversity(fx["sources"], f))["diversity_ratio"]
            for f in FRACTIONS
        ]
        print(_row(fx["topic"], vals))

    # --- source_authority: swap to low-authority (LLM-scored) ---
    from langchain_openai import ChatOpenAI
    grader = ChatOpenAI(temperature=0, model_name="gpt-4-turbo",
                        openai_api_key=os.environ["OPENAI_API_KEY"])
    print("\n=== source_authority  (swap to low-authority, LLM-scored) ===")
    print(_header())
    for fx in fixtures:
        vals = []
        for f in FRACTIONS:
            r = await metrics.source_authority(degrade_authority(fx["sources"], f), grader_model=grader)
            vals.append(r["avg_authority_score"])
        print(_row(fx["topic"], vals))

    # --- subtopic_coverage: remove sections, against a FIXED subtopic set ---
    print("\n=== subtopic_coverage  (remove report sections, fixed subtopics) ===")
    print(_header())
    for fx in fixtures:
        # Generate expected subtopics ONCE (from the full report), then reuse
        # them for every degradation level so coverage isn't confounded by
        # re-generation drift.
        base      = await metrics.subtopic_coverage(fx["query"], fx["report"], grader)
        subtopics = base.get("expected_subtopics", [])
        vals = []
        for f in FRACTIONS:
            r = await metrics.subtopic_coverage(
                fx["query"], degrade_subtopics(fx["report"], f), grader, subtopics=subtopics)
            vals.append(r.get("subtopic_coverage_rate"))
        print(_row(fx["topic"], vals))

    # --- unsupported_claim: corrupt a FIXED claim set (expect RISE) ---
    print("\n=== unsupported_claim  (corrupt fixed claim set, expect RISE) ===")
    print(_header())
    for fx in fixtures:
        # Extract claims ONCE, then corrupt a growing subset of the SAME set.
        base   = await metrics.unsupported_claim(fx["report"], fx["context"], grader)
        claims = [c["claim"] for c in base.get("breakdown", [])]
        vals = []
        for f in FRACTIONS:
            r = await metrics.unsupported_claim(
                fx["report"], fx["context"], grader, claims=corrupt_claims(claims, f))
            vals.append(r.get("unsupported_claim_rate"))
        print(_row(fx["topic"], vals, increasing=True))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # Load API key from file if not already set (needed for source_authority).
    if not os.getenv("OPENAI_API_KEY"):
        kp = Path("D:/chenh/api_keys/gpt_api_key.txt")
        if kp.exists():
            os.environ["OPENAI_API_KEY"] = kp.read_text().strip()
    asyncio.run(main())
