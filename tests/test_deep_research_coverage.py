import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest

from gpt_researcher.skills.deep_research import (
    count_words,
    trim_context_to_word_limit,
    ResearchProgress,
    DeepResearchSkill,
)


class TestCountWords:
    def test_string_input(self):
        assert count_words("hello world") == 2

    def test_list_input(self):
        assert count_words(["hello world", "foo bar"]) == 4

    def test_empty_string(self):
        assert count_words("") == 0

    def test_empty_list(self):
        assert count_words([]) == 0


class TestTrimContextToWordLimit:
    def test_within_limit(self):
        context = ["hello world", "foo bar"]
        result = trim_context_to_word_limit(context, max_words=100)
        assert result == ["hello world", "foo bar"]

    def test_exceeds_limit(self):
        context = ["this is way too long content " * 50, "short", "fit"]
        result = trim_context_to_word_limit(context, max_words=5)
        assert len(result) == 2
        assert result == ["short", "fit"]

    def test_preserves_recent_items(self):
        context = ["old " * 100, "medium " * 50, "new"]
        result = trim_context_to_word_limit(context, max_words=10)
        assert "new" in result

    def test_empty_input(self):
        assert trim_context_to_word_limit([], max_words=100) == []


class TestResearchProgress:
    def test_initialization(self):
        progress = ResearchProgress(total_depth=3, total_breadth=5)
        assert progress.total_depth == 3
        assert progress.total_breadth == 5
        assert progress.current_depth == 1
        assert progress.current_breadth == 0
        assert progress.total_queries == 0
        assert progress.completed_queries == 0


class FakeResearcherForDeep:
    def __init__(self):
        self.cfg = MagicMock()
        self.cfg.deep_research_breadth = 4
        self.cfg.deep_research_depth = 2
        self.cfg.deep_research_concurrency = 2
        self.cfg.strategic_llm_provider = "openai"
        self.cfg.strategic_llm_model = "gpt-4o-mini"
        self.cfg.reasoning_effort = "medium"
        self.cfg.config_path = None
        self.websocket = None
        self.tone = "objective"
        self.headers = {}
        self.visited_urls = set()
        self.retrievers = []


class TestDeepResearchSkillInit:
    def test_initialization(self):
        researcher = FakeResearcherForDeep()
        skill = DeepResearchSkill(researcher)
        assert skill.breadth == 4
        assert skill.depth == 2
        assert skill.concurrency_limit == 2
        assert skill.learnings == []
        assert skill.context == []


class TestGenerateSearchQueries:
    @pytest.mark.asyncio
    async def test_parses_query_goal_pairs(self):
        researcher = FakeResearcherForDeep()
        skill = DeepResearchSkill(researcher)

        with unittest.mock.patch(
            "gpt_researcher.skills.deep_research.create_chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = (
                "Query: AI trends 2026\n"
                "Goal: Find latest AI developments\n"
                "Query: Machine learning advances\n"
                "Goal: Research ML breakthroughs\n"
            )
            queries = await skill.generate_search_queries("test query", num_queries=2)
            assert len(queries) == 2
            assert queries[0]["query"] == "AI trends 2026"
            assert queries[0]["researchGoal"] == "Find latest AI developments"
            assert queries[1]["query"] == "Machine learning advances"

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty(self):
        researcher = FakeResearcherForDeep()
        skill = DeepResearchSkill(researcher)

        with unittest.mock.patch(
            "gpt_researcher.skills.deep_research.create_chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = ""
            queries = await skill.generate_search_queries("test", num_queries=3)
            assert queries == []


class TestGenerateResearchPlan:
    @pytest.mark.asyncio
    async def test_parses_questions(self):
        researcher = FakeResearcherForDeep()
        skill = DeepResearchSkill(researcher)

        with unittest.mock.patch(
            "gpt_researcher.skills.deep_research.create_chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = (
                "Question: What are the key trends?\n"
                "Question: How does this compare to last year?\n"
                "Question: What are the main challenges?\n"
            )
            questions = await skill.generate_research_plan("test", num_questions=3)
            assert len(questions) == 3
            assert "What are the key trends?" in questions

    @pytest.mark.asyncio
    async def test_retriever_error_silently_caught(self):
        researcher = FakeResearcherForDeep()

        class BrokenRetriever:
            __name__ = "BrokenRetriever"

            @staticmethod
            async def search(**kwargs):
                raise RuntimeError("retriever broken")

        researcher.retrievers = [BrokenRetriever]

        skill = DeepResearchSkill(researcher)

        with unittest.mock.patch(
            "gpt_researcher.skills.deep_research.create_chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = "Question: Test question?\n"
            questions = await skill.generate_research_plan("test", num_questions=1)
            assert len(questions) == 1
            assert "Test question" in questions[0]


class TestProcessResearchResults:
    @pytest.mark.asyncio
    async def test_parses_learnings_and_questions(self):
        researcher = FakeResearcherForDeep()
        skill = DeepResearchSkill(researcher)

        with unittest.mock.patch(
            "gpt_researcher.skills.deep_research.create_chat_completion",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = (
                "Learning [source1]: AI is advancing rapidly\n"
                "Question: What is next?\n"
            )
            result = await skill.process_research_results("test query", "some context", num_learnings=3)
            assert "learnings" in result
            assert result["learnings"] == ["AI is advancing rapidly"]


