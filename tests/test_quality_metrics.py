"""
Unit tests for evals/quality_eval/metrics.py

Covers:
  - Boundary conditions (empty inputs, zero values)
  - Correctness (math, domain parsing, rule table ordering)
  - Error / robustness paths (bad LLM JSON, LLM failure fallback)

Behavioral discrimination tests (good report > bad report) are handled by
the benchmark runner (evals/quality_eval/benchmark.py) using real reports.
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock

from evals.quality_eval.metrics import (
    citation_faithfulness,
    source_diversity,
    source_authority,
    subtopic_coverage,
    unsupported_claim,
    evaluate_report,
    is_skipped,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_model(*json_responses):
    """AsyncMock grader_model that returns each payload in sequence."""
    mock = AsyncMock()
    side_effects = []
    for payload in json_responses:
        msg = MagicMock()
        msg.content = json.dumps(payload)
        side_effects.append(msg)
    mock.ainvoke = AsyncMock(side_effect=side_effects)
    return mock


def _mock_model_raw(*raw_strings):
    """Like _mock_model but accepts pre-serialised strings (for error-path tests)."""
    mock = AsyncMock()
    side_effects = []
    for s in raw_strings:
        msg = MagicMock()
        msg.content = s
        side_effects.append(msg)
    mock.ainvoke = AsyncMock(side_effect=side_effects)
    return mock


def _mock_unsupported(claims, scored):
    """Mock for unsupported_claim's independent-verify path: one extract call
    returns `claims`, then one verify call PER claim returns that claim's
    [scored dict] (each verify now receives a single-element claim list)."""
    return _mock_model(claims, *[[s] for s in scored])


def _mock_subtopic(subtopics, covered_flags):
    """Mock for subtopic_coverage's independent-check path: generation returns
    `subtopics`, then one check call PER subtopic returns {"covered": bool}."""
    return _mock_model(subtopics, *[{"covered": c} for c in covered_flags])


# ---------------------------------------------------------------------------
# 1. citation_faithfulness  (Writing Behavior)
# ---------------------------------------------------------------------------

class TestCitationFaithfulness(unittest.TestCase):

    def test_no_references_section_returns_none(self):
        """Without a ## References section there is nothing to align against."""
        report = "The study found results ([nature](https://nature.com/a))."
        result = citation_faithfulness(report, ["https://nature.com/a"])
        self.assertIsNone(result["citation_faithfulness"])

    def test_all_listed_refs_cited_in_body_scores_one(self):
        report = (
            "Findings ([nature](https://nature.com/a)) and "
            "more ([bbc](https://bbc.com/b)).\n\n"
            "## References\n"
            "- A, [nature.com](https://nature.com/a)\n"
            "- B, [bbc.com](https://bbc.com/b)\n"
        )
        result = citation_faithfulness(report, ["https://nature.com/a", "https://bbc.com/b"])
        self.assertEqual(result["citation_faithfulness"], 1.0)
        self.assertEqual(result["listed_only_domains"], [])

    def test_listed_but_not_cited_lowers_faithfulness(self):
        """A source listed in References but never cited in body = misalignment."""
        report = (
            "Findings ([nature](https://nature.com/a)).\n\n"
            "## References\n"
            "- A, [nature.com](https://nature.com/a)\n"
            "- B, [bbc.com](https://bbc.com/b)\n"
        )
        result = citation_faithfulness(report, ["https://nature.com/a", "https://bbc.com/b"])
        # 1 of 2 listed refs is cited in body
        self.assertAlmostEqual(result["citation_faithfulness"], 0.5)
        self.assertIn("bbc.com", result["listed_only_domains"])
        self.assertNotIn("nature.com", result["listed_only_domains"])

    def test_www_prefix_aligns_body_and_refs(self):
        """www. normalization: nature.com in body aligns with www.nature.com in refs."""
        report = (
            "Findings ([nature](https://nature.com/a)).\n\n"
            "## References\n"
            "- A, [nature](https://www.nature.com/a)\n"
        )
        result = citation_faithfulness(report, ["https://nature.com/a"])
        self.assertEqual(result["citation_faithfulness"], 1.0)

    def test_coverage_is_descriptive_statistic(self):
        """citation_coverage = cited-in-body ∩ used / used (descriptive, not a score)."""
        report = (
            "Findings ([nature](https://nature.com/a)).\n\n"
            "## References\n- A, [nature.com](https://nature.com/a)\n"
        )
        sources = ["https://nature.com/a", "https://bbc.com/b"]
        result = citation_faithfulness(report, sources)
        # used = both (no context); only nature cited in body → coverage 0.5
        self.assertAlmostEqual(result["citation_coverage"], 0.5)

    def test_empty_sources_no_refs_returns_none(self):
        result = citation_faithfulness("plain report, no refs", [])
        self.assertIsNone(result["citation_faithfulness"])
        self.assertIsNone(result["citation_coverage"])


# ---------------------------------------------------------------------------
# 2. source_diversity
# ---------------------------------------------------------------------------

class TestSourceDiversity(unittest.TestCase):

    def test_empty_sources_returns_zeros(self):
        result = source_diversity([])
        self.assertEqual(result["diversity_ratio"], 0.0)
        self.assertEqual(result["domain_entropy"], 0.0)
        self.assertEqual(result["total_sources"], 0)

    def test_single_source_ratio_one_entropy_zero(self):
        result = source_diversity(["https://nature.com/a"])
        self.assertEqual(result["diversity_ratio"], 1.0)
        self.assertEqual(result["domain_entropy"], 0.0)

    def test_all_same_domain_entropy_zero(self):
        sources = ["https://blog.com/1", "https://blog.com/2", "https://blog.com/3"]
        result  = source_diversity(sources)
        self.assertAlmostEqual(result["domain_entropy"], 0.0, places=5)
        self.assertLess(result["diversity_ratio"], 0.5)

    def test_all_unique_domains_max_ratio(self):
        sources = [
            "https://nature.com/a", "https://bbc.com/b",
            "https://who.int/c",    "https://arxiv.org/d",
        ]
        result = source_diversity(sources)
        self.assertEqual(result["diversity_ratio"], 1.0)

    def test_entropy_higher_when_domains_spread(self):
        concentrated = source_diversity(
            ["https://blog.com/1", "https://blog.com/2",
             "https://blog.com/3", "https://other.com/4"]
        )
        spread = source_diversity(
            ["https://nature.com/1", "https://bbc.com/2",
             "https://who.int/3",    "https://arxiv.org/4"]
        )
        self.assertGreater(spread["domain_entropy"], concentrated["domain_entropy"])


# ---------------------------------------------------------------------------
# 3. source_authority  (rule-based path, no LLM)
# ---------------------------------------------------------------------------

class TestSourceAuthorityRules(unittest.IsolatedAsyncioTestCase):

    async def test_empty_sources_returns_zero(self):
        result = await source_authority([])
        self.assertEqual(result["avg_authority_score"], 0.0)
        self.assertEqual(result["breakdown"], [])

    async def test_gov_domains_score_one(self):
        result = await source_authority(["https://cdc.gov/page", "https://nih.gov/study"])
        self.assertAlmostEqual(result["avg_authority_score"], 1.0)

    async def test_edu_domains_score_high(self):
        result = await source_authority(["https://mit.edu/research"])
        self.assertGreaterEqual(result["avg_authority_score"], 0.85)

    async def test_gov_beats_com(self):
        gov = await source_authority(["https://cdc.gov/page"])
        com = await source_authority(["https://somesite.com/article"])
        self.assertGreater(gov["avg_authority_score"], com["avg_authority_score"])

    async def test_wikipedia_between_gov_and_com(self):
        gov  = await source_authority(["https://cdc.gov/page"])
        wiki = await source_authority(["https://en.wikipedia.org/wiki/Topic"])
        com  = await source_authority(["https://randomblog.com/post"])
        self.assertGreater(gov["avg_authority_score"],  wiki["avg_authority_score"])
        self.assertGreater(wiki["avg_authority_score"], com["avg_authority_score"])

    async def test_breakdown_length_matches_source_count(self):
        sources = ["https://nature.com/a", "https://bbc.com/b", "https://cdc.gov/c"]
        result  = await source_authority(sources)
        self.assertEqual(len(result["breakdown"]), 3)

    async def test_www_prefix_stripped_not_leading_chars(self):
        """Regression: www. must be stripped as a prefix, not as a char set.

        `"worldbank.org".lstrip("www.")` wrongly yields "orldbank.org", which
        breaks whitelist matching. removeprefix() keeps the domain intact.
        """
        result = await source_authority(["https://www.worldbank.org/report"])
        # worldbank.org is in the high-authority whitelist → 0.9
        self.assertAlmostEqual(result["avg_authority_score"], 0.9)
        self.assertEqual(result["breakdown"][0]["domain"], "worldbank.org")

    async def test_unknown_domain_uses_llm_score(self):
        llm_result = [{"domain": "obscuresite.io", "score": 0.65, "reason": "specialized blog"}]
        mock       = _mock_model(llm_result)
        result     = await source_authority(["https://obscuresite.io/article"], grader_model=mock)
        self.assertAlmostEqual(result["avg_authority_score"], 0.65)
        mock.ainvoke.assert_called_once()

    async def test_llm_failure_falls_back_to_default(self):
        mock = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=Exception("timeout"))
        result = await source_authority(["https://obscuresite.io/article"], grader_model=mock)
        self.assertAlmostEqual(result["avg_authority_score"], 0.4)


# ---------------------------------------------------------------------------
# 4. subtopic_coverage  (mocked LLM)
# ---------------------------------------------------------------------------

class TestSubtopicCoverage(unittest.IsolatedAsyncioTestCase):

    async def test_full_coverage_scores_one(self):
        subtopics = ["background", "causes", "effects", "timeline"]
        mock      = _mock_subtopic(subtopics, [True, True, True, True])
        result    = await subtopic_coverage("query", "report", mock)
        self.assertEqual(result["subtopic_coverage_rate"], 1.0)
        self.assertEqual(result["missing"], [])

    async def test_zero_coverage_scores_zero(self):
        subtopics = ["background", "causes", "effects"]
        mock      = _mock_subtopic(subtopics, [False, False, False])
        result    = await subtopic_coverage("query", "thin report", mock)
        self.assertEqual(result["subtopic_coverage_rate"], 0.0)

    async def test_partial_coverage_ratio(self):
        subtopics = ["A", "B", "C", "D"]
        mock      = _mock_subtopic(subtopics, [True, True, False, False])
        result    = await subtopic_coverage("query", "partial report", mock)
        self.assertAlmostEqual(result["subtopic_coverage_rate"], 0.5)

    async def test_empty_subtopics_returns_zero(self):
        mock   = _mock_subtopic([], [])
        result = await subtopic_coverage("narrow query", "report", mock)
        self.assertEqual(result["subtopic_coverage_rate"], 0.0)

    async def test_subtopic_extraction_failure_returns_error(self):
        mock   = _mock_model_raw("not json")
        result = await subtopic_coverage("query", "report", mock)
        self.assertIn("error", result)
        self.assertIsNone(result.get("subtopic_coverage_rate"))

    async def test_independent_subtopic_check_failure_marks_missing(self):
        """With independent checks, a subtopic whose check fails is marked
        missing (self-contained) rather than failing the whole evaluation."""
        subtopics = ["A", "B"]
        gen_msg   = MagicMock(); gen_msg.content = json.dumps(subtopics)   # generate
        ok_msg    = MagicMock(); ok_msg.content  = json.dumps({"covered": True})
        bad_msg   = MagicMock(); bad_msg.content = "{{broken"              # B check fails
        mock      = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[gen_msg, ok_msg, bad_msg])
        result = await subtopic_coverage("query", "report", mock)
        self.assertNotIn("error", result)
        self.assertEqual(result["expected_subtopics"], subtopics)
        self.assertAlmostEqual(result["subtopic_coverage_rate"], 0.5)  # 1 ok, 1 failed→missing


# ---------------------------------------------------------------------------
# 5. unsupported_claim  (mocked LLM)
# ---------------------------------------------------------------------------

class TestUnsupportedClaim(unittest.IsolatedAsyncioTestCase):

    def _scored(self, items):
        return [
            {"claim": c, "category": cat, "score": score, "reason": "test"}
            for c, cat, score in items
        ]

    async def test_all_supported_zero_unsupported_rate(self):
        claims = ["A", "B"]
        scored = self._scored([("A", "supported", 1.0), ("B", "supported", 1.0)])
        result = await unsupported_claim("report", "context", _mock_unsupported(claims, scored))
        self.assertEqual(result["unsupported_claim_rate"], 0.0)
        self.assertEqual(result["avg_claim_score"], 1.0)
        self.assertEqual(result["supported_count"], 2)

    async def test_all_unsupported_rate_one_score_zero(self):
        claims = ["X", "Y", "Z"]
        scored = self._scored([("X", "unsupported", 0.0), ("Y", "unsupported", 0.0),
                                ("Z", "unsupported", 0.0)])
        result = await unsupported_claim("report", "context", _mock_unsupported(claims, scored))
        self.assertEqual(result["unsupported_claim_rate"], 1.0)
        self.assertEqual(result["avg_claim_score"], 0.0)

    async def test_three_way_classification_counts(self):
        claims = ["A", "B", "C"]
        scored = self._scored([
            ("A", "supported",   1.0),
            ("B", "inferred",    0.7),
            ("C", "unsupported", 0.0),
        ])
        result = await unsupported_claim("report", "context", _mock_unsupported(claims, scored))
        self.assertEqual(result["supported_count"],   1)
        self.assertEqual(result["inferred_count"],    1)
        self.assertEqual(result["unsupported_count"], 1)
        self.assertAlmostEqual(result["inferred_claim_rate"],    1 / 3, places=2)
        self.assertAlmostEqual(result["unsupported_claim_rate"], 1 / 3, places=2)

    async def test_avg_score_computed_correctly(self):
        claims = ["A", "B"]
        scored = self._scored([("A", "supported", 1.0), ("B", "inferred", 0.6)])
        result = await unsupported_claim("report", "context", _mock_unsupported(claims, scored))
        self.assertAlmostEqual(result["avg_claim_score"], 0.8)

    async def test_empty_claims_returns_zero_no_crash(self):
        result = await unsupported_claim("report", "context", _mock_unsupported([], []))
        self.assertEqual(result["total_claims"], 0)
        self.assertEqual(result["avg_claim_score"], 0.0)
        self.assertNotIn("error", result)

    async def test_claim_extraction_failure_returns_error(self):
        result = await unsupported_claim("report", "context", _mock_model_raw("not json"))
        self.assertIn("error", result)
        self.assertIsNone(result.get("avg_claim_score"))

    async def test_independent_verify_failure_marks_claim_unsupported(self):
        """With independent scoring, a claim whose verify fails is marked
        unsupported (self-contained) rather than failing the whole batch."""
        claims   = ["Claim A"]
        good_msg = MagicMock(); good_msg.content = json.dumps(claims)   # extract
        bad_msg  = MagicMock(); bad_msg.content  = "{{broken"           # verify A fails
        mock     = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[good_msg, bad_msg])
        result = await unsupported_claim("report", "context", mock)
        self.assertEqual(result["total_claims"], 1)
        self.assertEqual(result["unsupported_count"], 1)
        self.assertNotIn("error", result)


# ---------------------------------------------------------------------------
# 6. evaluate_report  (orchestration shared by run_eval + benchmark)
# ---------------------------------------------------------------------------

class TestEvaluateReport(unittest.IsolatedAsyncioTestCase):

    async def test_flags_gate_llm_metrics(self):
        # nature.com is whitelisted → authority needs no LLM; flags off → no LLM at all.
        mock   = AsyncMock()
        result = await evaluate_report(
            "See https://nature.com/a", ["https://nature.com/a"], "ctx", "query", mock,
            run_subtopic=False, run_unsupported=False,
        )
        self.assertIn("citation_faithfulness", result)
        self.assertIn("source_diversity", result)
        self.assertIn("source_authority", result)
        self.assertIsNone(result["subtopic_coverage"])
        self.assertIsNone(result["unsupported_claim"])
        mock.ainvoke.assert_not_called()

    async def test_no_context_skips_unsupported(self):
        mock   = AsyncMock()
        result = await evaluate_report(
            "See https://nature.com/a", ["https://nature.com/a"], "", "query", mock,
            run_subtopic=False, run_unsupported=True,
        )
        self.assertTrue(is_skipped(result["unsupported_claim"]))
        mock.ainvoke.assert_not_called()  # empty context → skipped before any call


if __name__ == "__main__":
    unittest.main()
