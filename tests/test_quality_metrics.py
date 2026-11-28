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
from evals.quality_eval.base import EvalSample
from evals.quality_eval.pipeline_probe import PipelineTrace
from evals.quality_eval.suite import (
    CitationFaithfulnessMetric,
    UnsupportedClaimMetric,
    evaluate,
    default_metrics,
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
        self.assertEqual(result["llm_unscored_domains"], ["obscuresite.io"])

    async def test_llm_failure_uses_the_no_grader_rule_scores(self):
        """A failed call scores like no grader at all, not a flat 0.4."""
        mock = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=Exception("timeout"))
        urls = ["https://example.org/a", "https://example.com/b"]
        failed  = await source_authority(urls, grader_model=mock)
        no_llm  = await source_authority(urls)
        self.assertEqual(failed["avg_authority_score"], no_llm["avg_authority_score"])
        self.assertEqual(no_llm["llm_unscored_domains"], [])

    async def test_llm_domain_key_is_normalised(self):
        llm_result = [{"domain": "WWW.Obscuresite.io", "score": 0.65, "reason": "blog"}]
        result = await source_authority(["https://obscuresite.io/a"], grader_model=_mock_model(llm_result))
        self.assertAlmostEqual(result["avg_authority_score"], 0.65)


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

    async def test_subtopic_cache_reuses_the_expected_set(self):
        """A cached query must not regenerate its yardstick.

        Scoring the same query twice used to draw a fresh expected-subtopic list
        each time, so repeat runs were partly measuring generation drift.
        """
        subtopics = ["A", "B"]
        cache = {}

        first = _mock_subtopic(subtopics, [True, True])
        r1 = await subtopic_coverage("query", "report", first, subtopic_cache=cache)
        self.assertEqual(cache["query"], subtopics)
        self.assertEqual(first.ainvoke.call_count, 3)      # 1 generate + 2 checks

        # Second run: only coverage checks are queued, so a generation call
        # would consume a check payload and change the outcome.
        second = _mock_model({"covered": True}, {"covered": False})
        r2 = await subtopic_coverage("query", "report", second, subtopic_cache=cache)
        self.assertEqual(second.ainvoke.call_count, 2)     # no generate
        self.assertEqual(r1["expected_subtopics"], r2["expected_subtopics"])
        self.assertAlmostEqual(r2["subtopic_coverage_rate"], 0.5)

    async def test_missing_subtopics_split_into_retrieval_and_writing_gaps(self):
        """A subtopic nobody searched for is a planning failure, not a writing one."""
        subtopics = ["A", "B", "C"]
        mock = _mock_model(
            subtopics,
            {"covered": True}, {"covered": False}, {"covered": False},
            {"covered_by_search": False},   # B was never searched -> retrieval
            {"covered_by_search": True},    # C was searched -> writing
        )
        result = await subtopic_coverage("query", "report", mock,
                                         subqueries=["some search"])
        gaps = {d["subtopic"]: d["gap"] for d in result["missing_breakdown"]}
        self.assertEqual(gaps, {"B": "retrieval", "C": "writing"})
        self.assertEqual(result["retrieval_gap_rate"], 0.333)   # 1 of 3 expected

    async def test_no_gap_classification_without_subqueries(self):
        """Without the agent's searches the split is unknowable, so it is omitted."""
        mock = _mock_subtopic(["A", "B"], [True, False])
        result = await subtopic_coverage("query", "report", mock)
        self.assertNotIn("missing_breakdown", result)
        self.assertNotIn("retrieval_gap_rate", result)

    async def test_references_section_excluded_from_coverage_judgement(self):
        """Regression: the trailing `## References` list must not reach the grader.

        Source titles routinely contain the subtopic's own keywords, so leaving
        the list in let a report score coverage it never wrote — a report that
        was nothing but its reference list scored 43-57% covered.
        """
        subtopics = ["quantum error correction"]
        report = (
            "# Report\n\n"
            "The agent found little to say.\n\n"
            "## References\n\n"
            "Smith (2024). A complete survey of quantum error correction. "
            "https://example.com/qec\n"
        )
        mock = _mock_subtopic(subtopics, [False])
        await subtopic_coverage("query", report, mock)

        # call 0 generates the subtopics; the rest judge coverage
        judged = [call.args[0] for call in mock.ainvoke.call_args_list[1:]]
        self.assertTrue(judged, "expected at least one coverage-check call")
        for prompt in judged:
            self.assertNotIn("## References", prompt)
            self.assertNotIn("A complete survey of quantum error correction", prompt)
            self.assertIn("The agent found little to say", prompt)

    async def test_subtopic_extraction_failure_returns_error(self):
        mock   = _mock_model_raw("not json")
        result = await subtopic_coverage("query", "report", mock)
        self.assertIn("error", result)
        self.assertIsNone(result.get("subtopic_coverage_rate"))

    async def test_independent_subtopic_check_failure_is_excluded(self):
        """A subtopic whose check fails neither fails the whole evaluation nor
        counts as missing: it is reported under judge_errors and left out of
        the rate, so a grader outage does not read as a thin report."""
        subtopics = ["A", "B"]
        gen_msg   = MagicMock(); gen_msg.content = json.dumps(subtopics)   # generate
        ok_msg    = MagicMock(); ok_msg.content  = json.dumps({"covered": True})
        bad_msg   = MagicMock(); bad_msg.content = "{{broken"              # B check fails
        mock      = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[gen_msg, ok_msg, bad_msg])
        result = await subtopic_coverage("query", "report", mock)
        self.assertNotIn("error", result)
        self.assertEqual(result["expected_subtopics"], subtopics)
        self.assertAlmostEqual(result["subtopic_coverage_rate"], 1.0)  # 1 ok, 1 failed→excluded
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["judge_errors"], ["B"])

    async def test_all_subtopic_checks_failing_gives_no_rate(self):
        gen_msg = MagicMock(); gen_msg.content = json.dumps(["A", "B"])
        mock    = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[gen_msg, RuntimeError("down"), RuntimeError("down")])
        result = await subtopic_coverage("query", "report", mock)
        self.assertIsNone(result["subtopic_coverage_rate"])
        self.assertIn("error", result)

    async def test_subtopic_generation_must_be_a_list(self):
        gen_msg = MagicMock(); gen_msg.content = json.dumps({"subtopics": ["A"]})
        mock    = AsyncMock(); mock.ainvoke = AsyncMock(return_value=gen_msg)
        result = await subtopic_coverage("query", "report", mock)
        self.assertIsNone(result["subtopic_coverage_rate"])


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

    async def test_independent_verify_failure_is_excluded(self):
        """A claim whose verify fails neither fails the whole batch nor counts
        as unsupported: it is kept in the breakdown as "error" and left out of
        the rates."""
        claims   = ["Claim A", "Claim B"]
        good_msg = MagicMock(); good_msg.content = json.dumps(claims)   # extract
        ok_msg   = MagicMock(); ok_msg.content   = json.dumps(
            [{"claim": "restated A", "category": "supported", "score": 1.0, "reason": "r"}])
        bad_msg  = MagicMock(); bad_msg.content  = "{{broken"           # verify B fails
        mock     = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[good_msg, ok_msg, bad_msg])
        result = await unsupported_claim("report", "context", mock)
        self.assertEqual(result["total_claims"], 1)
        self.assertEqual(result["unsupported_count"], 0)
        self.assertEqual(result["judge_errors"], 1)
        self.assertEqual(result["avg_claim_score"], 1.0)
        self.assertNotIn("error", result)
        # The breakdown names the claim that was asked about, not the restatement.
        self.assertEqual([c["claim"] for c in result["breakdown"]], claims)
        self.assertEqual(result["breakdown"][1]["category"], "error")

    async def test_all_verifies_failing_gives_no_score(self):
        good_msg = MagicMock(); good_msg.content = json.dumps(["Claim A"])
        mock     = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[good_msg, RuntimeError("down")])
        result = await unsupported_claim("report", "context", mock)
        self.assertIsNone(result["avg_claim_score"])
        self.assertIn("error", result)

    async def test_unknown_category_is_an_error_not_a_verdict(self):
        good_msg = MagicMock(); good_msg.content = json.dumps(["Claim A", "Claim B"])
        odd_msg  = MagicMock(); odd_msg.content  = json.dumps(
            [{"claim": "A", "category": "partially", "score": 0.5}])
        ok_msg   = MagicMock(); ok_msg.content   = json.dumps(
            [{"claim": "B", "category": "unsupported", "score": 0.0}])
        mock     = AsyncMock()
        mock.ainvoke = AsyncMock(side_effect=[good_msg, odd_msg, ok_msg])
        result = await unsupported_claim("report", "context", mock)
        self.assertEqual(result["total_claims"], 1)
        self.assertEqual(result["unsupported_claim_rate"], 1.0)
        self.assertEqual(result["judge_errors"], 1)


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


# ---------------------------------------------------------------------------
# 7. suite  (BaseMetric wrappers + evaluate() entry point)
# ---------------------------------------------------------------------------

class TestSuite(unittest.IsolatedAsyncioTestCase):

    async def test_wrapper_standardizes_output_and_tags_metadata(self):
        report = ("Findings ([n](https://nature.com/a)).\n\n"
                  "## References\n- A, [nature.com](https://nature.com/a)\n")
        sample = EvalSample(query="q", report=report,
                            sources=["https://nature.com/a"], context="ctx")
        r = await CitationFaithfulnessMetric().measure(sample)
        self.assertEqual(r.name, "citation_faithfulness")
        self.assertEqual(r.group, "Citation")
        self.assertIn("ALCE", r.aligned_with)
        self.assertEqual(r.score, 1.0)         # standardized scalar
        self.assertFalse(r.skipped)
        self.assertIn("listed_only_domains", r.breakdown)   # raw detail preserved

    async def test_score_is_higher_is_better(self):
        # unsupported metric exposes avg_claim_score (higher=better), NOT the rate
        claims = ["A", "B"]
        scored = [{"claim": "A", "category": "supported", "score": 1.0, "reason": "t"},
                  {"claim": "B", "category": "supported", "score": 1.0, "reason": "t"}]
        r = await UnsupportedClaimMetric().measure(
            EvalSample(report="r", context="c"), _mock_unsupported(claims, scored))
        self.assertEqual(r.score, 1.0)         # all supported → high score
        self.assertEqual(r.group, "Faithfulness")

    async def test_missing_context_skips_not_aborts(self):
        r = await UnsupportedClaimMetric().measure(
            EvalSample(report="r", context=""), grader_model=AsyncMock())
        self.assertTrue(r.skipped)
        self.assertIsNone(r.score)

    async def test_evaluate_runs_selected_and_flags_gate(self):
        sample = EvalSample(query="q", report="See https://nature.com/a",
                            sources=["https://nature.com/a"], context="ctx")
        results = await evaluate(
            sample, default_metrics(run_subtopic=False, run_unsupported=False),
            grader_model=AsyncMock())
        self.assertEqual({r.name for r in results},
                         {"citation_faithfulness", "source_diversity", "source_authority"})
        for r in results:                       # every result is uniformly tagged
            self.assertTrue(r.group and r.aligned_with)


# ---------------------------------------------------------------------------
# 8. PipelineTrace  (per-stage funnel; pure recording, no pipeline needed)
# ---------------------------------------------------------------------------

class TestPipelineTrace(unittest.TestCase):

    def _trace(self):
        t = PipelineTrace()
        t.subqueries = ["q1", "q2"]
        # 3 attempted, 2 returned content
        t.record_scrape(
            ["https://a.gov/x", "https://b.com/y", "https://c.edu/z"],
            [{"url": "https://b.com/y", "raw_content": "b" * 500},
             {"url": "https://c.edu/z", "raw_content": "c" * 500}])
        return t

    def test_scrape_rate_counts_only_pages_that_returned_content(self):
        f = self._trace().funnel()
        self.assertEqual((f["urls_attempted"], f["urls_scraped"]), (3, 2))
        self.assertAlmostEqual(f["scrape_rate"], 0.667)

    def test_scraped_and_failed_urls_partition_the_attempts(self):
        t = self._trace()
        self.assertEqual(t.scraped_urls, ["https://b.com/y", "https://c.edu/z"])
        self.assertEqual(t.failed_urls, ["https://a.gov/x"])
        self.assertEqual(len(t.scraped_urls) + len(t.failed_urls),
                         len(set(t.attempted_urls)))

    def test_scraped_urls_deduplicates_across_batches(self):
        t = self._trace()
        t.record_scrape(["https://b.com/y"],
                        [{"url": "https://b.com/y", "raw_content": "again"}])
        self.assertEqual(t.scraped_urls.count("https://b.com/y"), 1)

    def test_search_overlap_counts_results_already_seen(self):
        """De-duplication happens before scraping, so a sub-query that returned
        nothing new is invisible downstream — this is the only stage where a
        wasted search slot can still be counted."""
        t = PipelineTrace()
        t.record_search(["a", "b", "c", "d"], ["a", "b", "c", "d"])   # all new
        t.record_search(["a", "b", "e", "f"], ["e", "f"])             # half seen
        f = t.funnel()
        self.assertEqual((f["urls_proposed"], f["urls_duplicate"]), (8, 2))
        self.assertAlmostEqual(f["search_overlap"], 0.25)

    def test_search_overlap_none_when_no_searches_recorded(self):
        self.assertIsNone(PipelineTrace().funnel()["search_overlap"])

    def test_compression_rate_is_context_over_corpus(self):
        t = PipelineTrace()
        t.record_compression("q", [{"raw_content": "x" * 10000}], 2500)
        self.assertAlmostEqual(t.funnel()["compression_rate"], 0.25)

    def test_top_n_cap_flagged_only_when_it_binds(self):
        """More qualifying chunks than top_n admits means the count cap did the
        cutting, not the similarity threshold."""
        t = PipelineTrace()
        t.record_compression("bound", [{"raw_content": "x" * 90000}], 100,
                             docs_after_filter=37, top_n=10)
        t.record_compression("slack", [{"raw_content": "x" * 90000}], 100,
                             docs_after_filter=4, top_n=10)
        self.assertEqual(t.funnel()["top_n_capped_calls"], 1)

    def test_fast_path_predicate_matches_the_compressor(self):
        t = PipelineTrace()
        t.record_compression("small", [{"raw_content": "x" * 1000}], 900)
        t.record_compression("large", [{"raw_content": "x" * 90000}], 900)
        self.assertEqual([c["fast_path"] for c in t.compressions], [True, False])
        self.assertEqual(t.funnel()["fast_path_calls"], 1)


if __name__ == "__main__":
    unittest.main()
