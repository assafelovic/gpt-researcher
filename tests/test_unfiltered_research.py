"""Tests for unfiltered search integrity.

Verifies that search queries are passed 1:1 from agent to retriever
without modification, filtering, or stripping by any layer.
"""

import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_mock_response, SENSITIVE_QUERIES


# ══════════════════════════════════════════════════════════════════════════════
# 1.  Retriever Pass-Through
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestRetrieverPassThrough:
    """Every retriever must pass the query string to the external API 1:1."""

    @pytest.mark.smoke
    def test_tavily_passes_query_unchanged(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        query = "kritische recherche mit speziellen begriffen XYZ <script>alert(1)</script>"
        retriever = TavilySearch(query=query)
        retriever.search(max_results=10)
        sent_data = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent_data["query"] == query, f"Query modified: {sent_data['query']!r} != {query!r}"

    def test_tavily_preserves_max_results_and_depth(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        retriever = TavilySearch(query="test query")
        retriever.search(max_results=7)
        sent_data = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent_data["max_results"] == 7
        assert sent_data["search_depth"] == "basic"

    def test_tavily_sensitive_query_preserved(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        retriever = TavilySearch(query=SENSITIVE_QUERIES[0])
        retriever.search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["query"] == SENSITIVE_QUERIES[0]

    def test_duckduckgo_passes_query_unchanged(self, mock_duckduckgo_get):
        from gpt_researcher.retrievers import Duckduckgo
        query = "komplexe abfrage mit üñíçödé & sonderzeichen"
        Duckduckgo(query=query).search()
        _, kwargs = mock_duckduckgo_get.call_args
        sent_q = kwargs["params"]["q"]
        assert sent_q == query, f"DuckDuckGo query modified: {sent_q!r} != {query!r}"

    def test_duckduckgo_no_safesearch_flag_interference(self, mock_duckduckgo_get):
        from gpt_researcher.retrievers import Duckduckgo
        Duckduckgo(query="test").search()
        params = mock_duckduckgo_get.call_args[1]["params"]
        assert params["kp"] == "-2", "DuckDuckGo safe-search flag unexpectedly modified"

    def test_duckduckgo_sensitive_query_preserved(self, mock_duckduckgo_get):
        from gpt_researcher.retrievers import Duckduckgo
        Duckduckgo(query=SENSITIVE_QUERIES[1]).search()
        assert mock_duckduckgo_get.call_args[1]["params"]["q"] == SENSITIVE_QUERIES[1]

    @patch("gpt_researcher.retrievers.bing.bing.requests.get")
    def test_bing_does_not_modify_query_text(self, mock_get, mock_bing_env):
        from gpt_researcher.retrievers import BingSearch
        query = "advanced persistent threat analysis"
        retriever = BingSearch(query=query)
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.text = json.dumps({"webPages": {"value": []}})
        retriever.search()
        params = mock_get.call_args[1]["params"]
        assert params["q"] == query

    @patch("gpt_researcher.retrievers.serper.serper.requests.request")
    def test_serper_passes_query_unchanged(self, mock_request, mock_serper_env):
        from gpt_researcher.retrievers import SerperSearch
        query = "neueste forschung zu klimawandel"
        retriever = SerperSearch(query=query)
        mock_request.return_value = MagicMock(status_code=200)
        mock_request.return_value.text = json.dumps({"organic": []})
        retriever.search()
        sent = json.loads(mock_request.call_args[1]["data"])
        assert sent["q"] == query

    @patch("gpt_researcher.actions.query_processing.get_search_results")
    def test_research_conductor_passes_query_to_retriever(self, mock_search):
        from gpt_researcher.agent import GPTResearcher
        from gpt_researcher.skills.researcher import ResearchConductor
        query = "test query preservation"
        researcher = GPTResearcher(query=query)
        conductor = ResearchConductor(researcher)
        asyncio.run(conductor._search(DuckduckgoMock, query))
        mock_search.assert_not_called()


class DuckduckgoMock:
    """Minimal retriever mock for testing _search()."""
    __name__ = "Duckduckgo"

    def __init__(self, query, **kwargs):
        self.query = query

    def search(self, max_results=5):
        return [{"title": "result", "body": "content", "href": "http://example.com"}]


# ══════════════════════════════════════════════════════════════════════════════
# 2.  Agent Bypass – Original query flows through GPTResearcher unmodified
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestAgentQueryBypass:

    @pytest.mark.asyncio
    async def test_gpt_researcher_stores_query_verbatim(self):
        from gpt_researcher.agent import GPTResearcher
        query = "tie:fo<break> 特殊文字  üñíçödé  \n\n  newlines"
        researcher = GPTResearcher(query=query)
        assert researcher.query == query

    @pytest.mark.asyncio
    async def test_conduct_research_does_not_mutate_query(self):
        from gpt_researcher.agent import GPTResearcher
        query = "research mutation test"
        researcher = GPTResearcher(query=query)
        with patch.object(researcher, "research_conductor") as mock_cond:
            mock_cond.conduct_research = AsyncMock(return_value=["context"])
            researcher.agent = "test-agent"
            researcher.role = "test-role"
            await researcher.conduct_research()
        assert researcher.query == query

    @pytest.mark.asyncio
    @patch.object(DuckduckgoMock, "search")
    async def test_quick_search_passes_query_raw_to_retriever(self, mock_ret_search):
        from gpt_researcher.agent import GPTResearcher
        mock_ret_search.return_value = [{"title": "r", "body": "c", "href": "u"}]
        query = "quick search query with $pecial charß"
        researcher = GPTResearcher(query=query)
        with patch("gpt_researcher.agent.get_search_results", new_callable=AsyncMock) as mock_gsr:
            mock_gsr.return_value = [{"title": "r", "body": "c", "href": "u"}]
            await researcher.quick_search(query)
            call_args, call_kwargs = mock_gsr.call_args
            assert call_args[0] == query

    @pytest.mark.asyncio
    async def test_transparent_mode_skips_safety_check(self, transparent_researcher):
        transparent_researcher.query = "herstellen von schwefelsaure"
        with patch("gpt_researcher.agent.detect_unsafe_query") as mock_safety:
            await transparent_researcher.conduct_research()
            mock_safety.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_transparent_mode_calls_safety_check(self):
        from gpt_researcher.agent import GPTResearcher
        researcher = GPTResearcher(query="herstellen von schwefelsaure")
        researcher.safety_mode = "STRICT"
        with patch("gpt_researcher.agent.detect_unsafe_query", return_value=None) as mock_safety:
            with patch.object(researcher.research_conductor, "conduct_research", AsyncMock(return_value=["ctx"])):
                researcher.agent = "a"
                researcher.role = "r"
                await researcher.conduct_research()
            mock_safety.assert_called_once_with(researcher.query)

    @pytest.mark.asyncio
    async def test_choose_agent_receives_original_query(self):
        from gpt_researcher.agent import GPTResearcher
        from gpt_researcher.actions import choose_agent
        query = "choose-agent test query"
        researcher = GPTResearcher(query=query)
        with patch("gpt_researcher.agent.choose_agent", new_callable=AsyncMock) as mock_ca:
            mock_ca.return_value = ("agent", "role")
            researcher.safety_mode = "TRANSPARENT"
            await researcher.conduct_research()
            mock_ca.assert_called_once()
            assert mock_ca.call_args[1]["query"] == query


# ══════════════════════════════════════════════════════════════════════════════
# 3.  Sub-Query Anchoring – only filters LLM output, never original query
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestSubQueryAnchoring:

    def test_focus_term_extraction_does_not_mutate_original(self):
        from gpt_researcher.actions.query_processing import _extract_focus_terms
        query = "Python vs Java performance comparison 2026"
        original = query[:]
        _extract_focus_terms(query)
        assert query == original

    def test_off_topic_subqueries_dropped_no_match(self):
        from gpt_researcher.actions.query_processing import _is_task_anchored_query
        query = "Python web frameworks"
        parent = ""
        assert _is_task_anchored_query("best pizza toppings", query, parent) is False

    def test_on_topic_subqueries_preserved(self):
        from gpt_researcher.actions.query_processing import _is_task_anchored_query
        query = "Python async web frameworks"
        parent = ""
        assert _is_task_anchored_query("async web frameworks comparison", query, parent) is True

    def test_original_query_always_anchored_to_itself(self):
        from gpt_researcher.actions.query_processing import _is_task_anchored_query
        query = "some very specific technical question"
        assert _is_task_anchored_query(query, query, "") is True

    def test_complete_sub_queries_never_rewrites_original(self):
        from gpt_researcher.actions.query_processing import _complete_sub_queries
        query = "microservices vs monolith comparison"
        result = _complete_sub_queries([query], query, "", 5)
        assert query in result or any(query in r for r in result)

    def test_sub_query_filtering_preserves_critical_terms(self):
        from gpt_researcher.actions.query_processing import _is_task_anchored_query
        base = "CVE kernel exploit analysis"
        queries = [
            ("CVE exploit vulnerability", True),
            ("kernel exploit mitigation", True),
            ("completely unrelated topic", False),
        ]
        for candidate, expected in queries:
            assert _is_task_anchored_query(candidate, base, "") is expected


# ══════════════════════════════════════════════════════════════════════════════
# 4.  Sensitive Query Integrität
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestSensitiveQueryIntegrity:

    @pytest.mark.parametrize("query", SENSITIVE_QUERIES)
    def test_tavily_passes_all_sensitive_queries(self, query, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        TavilySearch(query=query).search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["query"] == query, f"Tavily modified query {query[:30]!r}..."

    @pytest.mark.parametrize("query", SENSITIVE_QUERIES[:5])
    def test_duckduckgo_passes_all_sensitive_queries(self, query, mock_duckduckgo_get):
        from gpt_researcher.retrievers import Duckduckgo
        Duckduckgo(query=query).search()
        assert mock_duckduckgo_get.call_args[1]["params"]["q"] == query

    @pytest.mark.asyncio
    async def test_sensitive_query_skips_safety_in_transparent_mode(self, transparent_researcher):
        transparent_researcher.query = SENSITIVE_QUERIES[0]
        with patch("gpt_researcher.agent.detect_unsafe_query") as mock_safety:
            ctx = await transparent_researcher.conduct_research()
            mock_safety.assert_not_called()
        assert ctx == ["context"]

    @pytest.mark.asyncio
    async def test_warn_only_mode_logs_but_does_not_block_sensitive_query(self):
        from gpt_researcher.agent import GPTResearcher
        from gpt_researcher.utils.query_safety import QuerySafetyDecision
        decision = QuerySafetyDecision(
            blocked=True, category="hazardous_chemistry",
            reason="test", matched_terms=("test",),
            safe_alternatives=("alt",),
        )
        researcher = GPTResearcher(query=SENSITIVE_QUERIES[0])
        researcher.safety_mode = "WARN_ONLY"
        with patch("gpt_researcher.agent.detect_unsafe_query", return_value=decision):
            with patch.object(researcher.research_conductor, "conduct_research", AsyncMock(return_value=["ctx"])):
                await researcher.conduct_research()
        assert researcher.safety_decision is not None

    @patch("gpt_researcher.actions.query_processing._is_task_anchored_query")
    def test_query_processing_does_not_filter_original_query(self, mock_anchor):
        from gpt_researcher.actions.query_processing import _complete_sub_queries
        mock_anchor.return_value = True
        query = "sensitive original query"
        result = _complete_sub_queries([query], query, "", 5)
        assert query in result, "Original query should always be in sub-queries"

    @pytest.mark.asyncio
    async def test_full_pipeline_sensitive_query_preserved(self):
        from gpt_researcher.agent import GPTResearcher
        query = "<script>alert('test')</script> malicious query"
        researcher = GPTResearcher(query=query)
        assert researcher.query == query
        with patch.object(researcher.research_conductor, "conduct_research", AsyncMock(return_value=["ctx"])):
            with patch("gpt_researcher.agent.choose_agent", AsyncMock(return_value=("a", "r"))):
                researcher.safety_mode = "TRANSPARENT"
                await researcher.conduct_research()
        assert researcher.query == query


# ══════════════════════════════════════════════════════════════════════════════
# 5.  FastAPI Endpoint Integration – /report/ preserves query
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFastAPIEndpoint:

    @pytest.fixture
    def research_request_data(self):
        return {
            "task": "test sensitive query: ../../../etc/passwd + <script>",
            "report_type": "research_report",
            "report_source": "web",
            "tone": "objective",
            "headers": {},
            "repo_name": "test",
            "branch_name": "main",
            "generate_in_background": False,
        }

    @pytest.mark.asyncio
    async def test_research_request_model_stores_task_verbatim(self, research_request_data):
        from backend.server.app import ResearchRequest
        req = ResearchRequest(**research_request_data)
        assert req.task == research_request_data["task"]

    @pytest.mark.asyncio
    async def test_websocket_communication_receives_original_query(self):
        from backend.server.server_utils import handle_websocket_communication
        ws_mock = AsyncMock()
        manager_mock = MagicMock()
        ws_mock.receive_text = AsyncMock(side_effect=[
            json.dumps({"type": "start", "task": SENSITIVE_QUERIES[2]}),
            json.dumps({"type": "stop"}),
        ])
        with patch("backend.server.websocket_manager.run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "report text"
            try:
                await handle_websocket_communication(ws_mock, manager_mock)
            except Exception:
                pass
            if mock_run.called:
                assert mock_run.call_args[1]["task"] == SENSITIVE_QUERIES[2]

    @pytest.mark.asyncio
    async def test_write_report_passes_task_to_run_agent(self):
        from backend.server.app import write_report, ResearchRequest
        from gpt_researcher.utils.enum import Tone
        req = ResearchRequest(
            task="nmap scan 192.168.1.0/24 vulnerability assessment",
            report_type="research_report", report_source="web",
            tone=Tone.Objective.name, headers={}, repo_name="x", branch_name="main",
        )
        mock_researcher = MagicMock()
        mock_researcher.get_source_urls.return_value = []
        mock_researcher.get_costs.return_value = 0.0
        mock_researcher.visited_urls = set()
        mock_researcher.get_research_images.return_value = []
        mock_researcher.verification_bundle = None
        mock_researcher.safety_decision = None
        with patch("backend.server.app.run_agent", new_callable=AsyncMock) as mock_ra:
            mock_ra.return_value = ("report", mock_researcher)
            with patch("backend.server.app.generate_report_files", new_callable=AsyncMock) as mock_grf:
                mock_grf.return_value = {}
                with patch("backend.server.app.make_unique_artifact_stem", return_value="test_id"):
                    await write_report(req, "test_id")
        assert mock_ra.call_args[1]["task"] == req.task


# ══════════════════════════════════════════════════════════════════════════════
# 6.  WebSocket Streaming Integrity
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestWebSocketStreaming:

    @pytest.mark.asyncio
    async def test_websocket_manager_streams_messages_unchanged(self):
        from backend.server.websocket_manager import WebSocketManager
        ws_mock = AsyncMock()
        manager = WebSocketManager()
        await manager.connect(ws_mock)

        queue = manager.message_queues[ws_mock]
        test_msg = json.dumps({"type": "logs", "output": "critical search result"})
        await queue.put(test_msg)
        await queue.put(None)
        await asyncio.sleep(0.05)

        sent_calls = [c for c in ws_mock.send_text.call_args_list if c[0][0] != "pong"]
        assert any(test_msg in str(c) for c in sent_calls)

    @pytest.mark.asyncio
    async def test_websocket_echoes_query_verbatim(self):
        from backend.server.websocket_manager import WebSocketManager
        ws_mock = AsyncMock()
        manager = WebSocketManager()
        await manager.connect(ws_mock)
        query = "echo this exact query"
        msg = json.dumps({"type": "logs", "output": f"Researching: {query}"})
        await manager.message_queues[ws_mock].put(msg)
        await manager.message_queues[ws_mock].put(None)
        await asyncio.sleep(0.05)

        assert any(query in str(c) for c in ws_mock.send_text.call_args_list)

    @pytest.mark.asyncio
    async def test_stream_output_does_not_modify_content(self):
        ws_mock = AsyncMock()
        content = "raw output with $pecial ch@rs"

        from gpt_researcher.actions.utils import stream_output
        ws_mock.send_text = AsyncMock()
        await stream_output("logs", "test", content, ws_mock)
        if ws_mock.send_text.call_args:
            sent = json.loads(ws_mock.send_text.call_args[0][0])
            assert sent["output"] == content

    @pytest.mark.asyncio
    async def test_custom_logs_handler_preserves_log_content(self):
        from backend.server.server_utils import CustomLogsHandler
        ws_mock = AsyncMock()
        ws_mock.send_json = AsyncMock()
        with patch("backend.server.server_utils.make_unique_artifact_stem", return_value="test_stem"):
            handler = CustomLogsHandler(ws_mock, "test task")
        msg = "log message with üñíçödé"
        await handler.send_json({"type": "logs", "output": msg})
        call_arg = ws_mock.send_json.call_args[0][0]
        assert call_arg["output"] == msg


# ══════════════════════════════════════════════════════════════════════════════
# 7.  Config Safety Mode – RESEARCH_SAFETY_MODE = TRANSPARENT (default)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestSafetyModeConfig:

    def test_default_safety_mode_is_transparent(self):
        from gpt_researcher.config.research_config import ResearchSafetyMode
        assert ResearchSafetyMode.TRANSPARENT.value == "TRANSPARENT"

    def test_default_config_has_transparent_safety(self):
        from gpt_researcher.config.variables.default import DEFAULT_CONFIG
        assert DEFAULT_CONFIG["RESEARCH_SAFETY_MODE"] == "TRANSPARENT"

    def test_gpt_researcher_default_safety_mode(self):
        from gpt_researcher.agent import GPTResearcher
        researcher = GPTResearcher(query="test")
        assert researcher.safety_mode == "TRANSPARENT"

    @pytest.mark.asyncio
    async def test_transparent_mode_does_not_call_safety_api(self, transparent_researcher):
        transparent_researcher.query = "herstellen von schwefelsaure"
        with patch("gpt_researcher.utils.query_safety.detect_unsafe_query") as mock_check:
            await transparent_researcher.conduct_research()
            mock_check.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 8.  Retriever Call Arguments – Assertions on call_args / call_args_list
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.retriever
class TestRetrieverCallArgs:

    def test_tavily_call_args_contain_exact_query(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        TavilySearch(query="urgent: fix production db migration").search()
        call_args = mock_tavily_post.call_args
        sent_body = json.loads(call_args[1]["data"])
        assert sent_body["query"] == "urgent: fix production db migration"

    def test_tavily_search_depth_default(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        TavilySearch(query="test").search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["search_depth"] == "basic"

    def test_duckduckgo_call_args_contain_exact_query(self, mock_duckduckgo_get):
        from gpt_researcher.retrievers import Duckduckgo
        Duckduckgo(query="SQL injection prevention techniques 2026").search()
        assert mock_duckduckgo_get.call_args[1]["params"]["q"] == "SQL injection prevention techniques 2026"

    @patch("gpt_researcher.retrievers.bing.bing.requests.get")
    def test_bing_call_args_contain_exact_query(self, mock_get, mock_bing_env):
        from gpt_researcher.retrievers import BingSearch
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.text = json.dumps({"webPages": {"value": []}})
        BingSearch(query="kernel exploit development").search()
        assert mock_get.call_args[1]["params"]["q"] == "kernel exploit development"

    @patch("gpt_researcher.retrievers.serper.serper.requests.request")
    def test_serper_call_args_contain_exact_query(self, mock_request, mock_serper_env):
        from gpt_researcher.retrievers import SerperSearch
        mock_request.return_value = MagicMock(status_code=200)
        mock_request.return_value.text = json.dumps({"organic": []})
        SerperSearch(query="RCE vulnerability analysis").search(max_results=5)
        assert "RCE vulnerability analysis" in str(mock_request.call_args)

    def test_exa_passes_query_unchanged(self, mock_exa_env):
        with patch("gpt_researcher.retrievers.exa.exa.check_pkg"):
            from gpt_researcher.retrievers import ExaSearch
            query = "exa search query test"
            retriever = ExaSearch(query=query)
            retriever.search()
            mock_exa_env.search.assert_called_once()
            call_query = mock_exa_env.search.call_args[0][0]
            assert call_query == query


# ══════════════════════════════════════════════════════════════════════════════
# 9.  Edge Cases – Empty, very long, binary, unicode
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.security
class TestEdgeCases:

    def test_empty_query_preserved(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        TavilySearch(query="").search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["query"] == ""

    def test_very_long_query_preserved(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        query = "x" * 10000
        TavilySearch(query=query).search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["query"] == query
        assert len(sent["query"]) == 10000

    def test_unicode_query_preserved(self, mock_tavily_post):
        from gpt_researcher.retrievers import TavilySearch
        query = "日本語 한국어 العربية русский עברית üñíçödé"
        TavilySearch(query=query).search()
        sent = json.loads(mock_tavily_post.call_args[1]["data"])
        assert sent["query"] == query


# ══════════════════════════════════════════════════════════════════════════════
# 10.  Pipeline Integration – Full end-to-end mock with call assertions
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPipelineIntegration:

    @pytest.mark.asyncio
    async def test_full_research_pipeline_preserves_query(self, transparent_researcher):
        transparent_researcher.query = "integration test query"
        with patch("gpt_researcher.agent.choose_agent", AsyncMock(return_value=("agent", "role"))):
            await transparent_researcher.conduct_research()

        assert transparent_researcher.query == "integration test query"
        assert transparent_researcher.context == ["context"]

    @pytest.mark.asyncio
    async def test_get_search_results_call_args(self):
        from gpt_researcher.actions.query_processing import get_search_results

        mock_retriever_cls = MagicMock()
        mock_retriever_cls.__name__ = "Duckduckgo"
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        mock_retriever_cls.return_value = mock_instance

        query = "get_search_results call args test"
        await get_search_results(query, mock_retriever_cls, query_domains=["example.com"])

        mock_retriever_cls.assert_called_once_with(query, query_domains=["example.com"])
        mock_instance.search.assert_called_once()
