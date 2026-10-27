"""Offline tests for the quality_eval runners and the pipeline probe's hooks.

The runners are exercised end to end with a fake researcher and a fake
grader, so a broken import, a renamed field or a crash in the console
summary shows up here instead of halfway through a paid run. The hook tests
fail when an upstream refactor removes or reshapes a method the probe
patches, which would otherwise make the probe record nothing, silently.
"""

import inspect
import json
import unittest

from evals.quality_eval.pipeline_probe import PipelineProbe, PipelineTrace, sources_to_score

REPORT = """# Report

Intro citing [NIH](https://www.nih.gov/a) and [Nature](https://nature.com/b).

## Section A
Treatment uptake increased by 20% ([Mayo](https://mayoclinic.org/c)).

## References
- [NIH](https://www.nih.gov/a)
- [Nature](https://nature.com/b)
"""
SOURCES = ["https://www.nih.gov/a", "https://nature.com/b", "https://mayoclinic.org/c"]
CONTEXT = "Source: https://www.nih.gov/a\nTreatment uptake increased by 20%."


class _Resp:
    def __init__(self, content):
        self.content = content


class _FakeGrader:
    """Answers each quality_eval prompt with a well-formed reply, or raises."""

    def __init__(self, fail: bool = False):
        self.fail = fail

    async def ainvoke(self, prompt):
        if self.fail:
            raise RuntimeError("grader unavailable")
        if "List the key subtopics" in prompt:
            return _Resp(json.dumps(["treatments", "outcomes"]))
        if "single subtopic" in prompt:
            return _Resp(json.dumps({"covered": True}))
        if "Extract specific, verifiable" in prompt:
            return _Resp(json.dumps(["Uptake increased by 20%"]))
        if "credibility score" in prompt:
            return _Resp(json.dumps([{"claim": "x", "category": "supported", "score": 1.0}]))
        if "Rate the authority" in prompt:
            return _Resp(json.dumps([{"domain": "mayoclinic.org", "score": 0.9, "reason": "clinic"}]))
        raise AssertionError(f"unexpected prompt: {prompt[:80]}")


class _FakeResearcher:
    def __init__(self, **kwargs):
        pass

    async def conduct_research(self):
        return CONTEXT

    async def write_report(self):
        return REPORT

    def get_source_urls(self):
        return SOURCES

    def get_costs(self):
        return 0.01


class TestSourcesToScore(unittest.TestCase):

    def test_scraped_pages_when_probe_saw_the_scrape_stage(self):
        t = PipelineTrace()
        t.record_scrape(SOURCES, [{"url": SOURCES[1], "raw_content": "x"}])
        self.assertEqual(sources_to_score(t, SOURCES), ([SOURCES[1]], "scraped"))

    def test_every_scrape_failing_scores_nothing_rather_than_falling_back(self):
        t = PipelineTrace()
        t.record_scrape(SOURCES, [])
        self.assertEqual(sources_to_score(t, SOURCES), ([], "scraped"))

    def test_falls_back_to_visited_only_when_probe_recorded_nothing(self):
        self.assertEqual(sources_to_score(PipelineTrace(), SOURCES), (SOURCES, "visited"))


class TestProbeHookContract(unittest.TestCase):
    """The methods PipelineProbe patches must exist with the arguments it passes."""

    def _params(self, fn):
        return list(inspect.signature(fn).parameters)

    def test_hook_targets_exist_with_expected_signatures(self):
        from gpt_researcher.prompts import PromptFamily
        from gpt_researcher.skills.browser import BrowserManager
        from gpt_researcher.skills.context_manager import ContextManager
        from gpt_researcher.skills.researcher import ResearchConductor

        self.assertTrue(inspect.iscoroutinefunction(ResearchConductor.plan_research))
        self.assertEqual(self._params(ResearchConductor.plan_research)[:2], ["self", "query"])
        self.assertTrue(inspect.iscoroutinefunction(ResearchConductor._get_new_urls))
        self.assertEqual(self._params(ResearchConductor._get_new_urls)[:2], ["self", "url_set_input"])
        self.assertTrue(inspect.iscoroutinefunction(BrowserManager.browse_urls))
        self.assertEqual(self._params(BrowserManager.browse_urls)[:2], ["self", "urls"])
        self.assertTrue(inspect.iscoroutinefunction(ContextManager.get_similar_content_by_query))
        self.assertEqual(self._params(ContextManager.get_similar_content_by_query)[:3],
                         ["self", "query", "pages"])
        self.assertIsInstance(inspect.getattr_static(PromptFamily, "pretty_print_docs"), staticmethod)
        self.assertEqual(self._params(PromptFamily.pretty_print_docs), ["docs", "top_n"])

    def test_probe_restores_the_originals(self):
        from gpt_researcher.prompts import PromptFamily
        from gpt_researcher.skills.browser import BrowserManager

        before = (BrowserManager.browse_urls, inspect.getattr_static(PromptFamily, "pretty_print_docs"))
        with PipelineProbe():
            self.assertIsNot(BrowserManager.browse_urls, before[0])
        after = (BrowserManager.browse_urls, inspect.getattr_static(PromptFamily, "pretty_print_docs"))
        self.assertIs(after[0], before[0])
        self.assertIs(after[1].__func__, before[1].__func__)


class TestRunEvalOffline(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        from evals.quality_eval import run_eval
        self.run_eval = run_eval
        self._orig = run_eval.GPTResearcher
        run_eval.GPTResearcher = _FakeResearcher

    async def asyncTearDown(self):
        self.run_eval.GPTResearcher = self._orig

    async def test_all_metrics_score_with_a_working_grader(self):
        r = await self.run_eval.evaluate_single_query("q?", _FakeGrader(), True, False, True)
        self.assertEqual(r["subtopic_coverage"]["subtopic_coverage_rate"], 1.0)
        self.assertEqual(r["unsupported_claim"]["avg_claim_score"], 1.0)
        self.assertEqual(r["unsupported_claim"]["breakdown"][0]["claim"], "Uptake increased by 20%")
        # The fake researcher never reaches the scrape stage, so the fallback is labelled.
        self.assertEqual(r["sources_basis"], "visited")

    async def test_grader_outage_skips_metrics_instead_of_scoring_zero(self):
        r = await self.run_eval.evaluate_single_query("q?", _FakeGrader(fail=True), True, False, True)
        self.assertEqual(r["subtopic_coverage"]["status"], "skipped")
        self.assertEqual(r["unsupported_claim"]["status"], "skipped")
        self.assertEqual(r["source_authority"]["llm_unscored_domains"], ["mayoclinic.org"])
        # The real cause is reported, not a generic "failed to parse".
        self.assertIn("grader unavailable", r["subtopic_coverage"]["reason"])


class TestJudge(unittest.TestCase):

    def test_env_override_is_read_at_call_time(self):
        import os
        from unittest import mock
        from evals.judge import DEFAULT_JUDGE_MODEL, judge_model_name

        with mock.patch.dict(os.environ, {"EVAL_JUDGE_MODEL": "gpt-4o"}):
            self.assertEqual(judge_model_name(), "gpt-4o")
        with mock.patch.dict(os.environ, {"EVAL_JUDGE_MODEL": ""}):
            self.assertEqual(judge_model_name(), DEFAULT_JUDGE_MODEL)

    def test_reasoning_models_get_no_temperature(self):
        import os
        from unittest import mock
        from evals.judge import make_judge

        # ChatOpenAI refuses to build without a key; no call is made.
        mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}).start()
        self.addCleanup(mock.patch.stopall)
        self.assertEqual(make_judge("gpt-4o").temperature, 0)
        self.assertIsNone(make_judge("gpt-5.4-mini").temperature)
        self.assertIsNone(make_judge("gpt-6-luna").temperature)


class TestBenchmarkOffline(unittest.IsolatedAsyncioTestCase):

    async def test_single_agent_query_evaluates(self):
        from evals.quality_eval import benchmark

        async def fake_single(query, model):
            return REPORT, SOURCES, CONTEXT, 0.01

        orig = benchmark._run_single_agent
        benchmark._run_single_agent = fake_single
        try:
            r = await benchmark._evaluate_query(
                "medical", "q?", {"arch": "single", "model": "m"}, _FakeGrader(), True, {})
        finally:
            benchmark._run_single_agent = orig
        self.assertNotIn("error", r)
        self.assertEqual(r["sources_basis"], "visited")
        self.assertEqual(r["subtopic_coverage"]["subtopic_coverage_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
