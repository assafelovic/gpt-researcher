import pytest


from gpt_researcher.utils.costs import estimate_llm_cost, estimate_embedding_cost
from gpt_researcher.utils.artifacts import make_unique_artifact_stem
from gpt_researcher.utils.validators import Subtopics
from gpt_researcher.utils.rate_limiter import GlobalRateLimiter, get_global_rate_limiter


class TestCostEstimates:
    def test_estimate_llm_cost_known_model(self):
        cost = estimate_llm_cost("hello " * 100, "world " * 50)
        assert isinstance(cost, float)
        assert cost > 0

    def test_estimate_llm_cost_unknown_model(self):
        cost = estimate_llm_cost("", "")
        assert cost == 0

    def test_estimate_embedding_cost(self):
        cost = estimate_embedding_cost(model="text-embedding-3-large", docs=[{"raw_content": "hello world"}])
        assert isinstance(cost, float)


class TestArtifacts:
    def test_make_unique_artifact_stem(self):
        stem = make_unique_artifact_stem("task", "test query")
        assert "task" in stem
        assert len(stem) > 10

    def test_make_unique_artifact_stem_different_inputs(self):
        stem1 = make_unique_artifact_stem("task1", "query1")
        stem2 = make_unique_artifact_stem("task2", "query2")
        assert stem1 != stem2


class TestSubtopicsValidator:
    def test_subtopics_valid(self):
        st = Subtopics(subtopics=[{"task": "topic1"}])
        assert len(st.subtopics) == 1
        assert st.subtopics[0].task == "topic1"


class TestGlobalRateLimiter:
    def test_singleton(self):
        rl1 = GlobalRateLimiter()
        rl2 = GlobalRateLimiter()
        assert rl1 is rl2

    def test_configure(self):
        rl = GlobalRateLimiter()
        rl.configure(0.5)
        assert rl.rate_limit_delay == 0.5

    def test_reset(self):
        rl = GlobalRateLimiter()
        rl.last_request_time = 100.0
        rl.reset()
        assert rl.last_request_time == 0.0

    def test_singleton_instance(self):
        limiter = get_global_rate_limiter()
        assert isinstance(limiter, GlobalRateLimiter)