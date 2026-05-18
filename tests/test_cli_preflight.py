import io
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from unittest.mock import AsyncMock, patch

import cli


class SuccessfulProbeRetriever:
    queries = []

    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []
        self.last_rate_limit_remaining = "42"
        self.last_rate_limit_reset = "3600"
        SuccessfulProbeRetriever.queries.append(query)

    def search(self, max_results=3):
        return [{"href": "https://example.com", "body": "result"}]


class SecondProbeFailsRetriever:
    queries = []

    def __init__(self, query, query_domains=None):
        self.query = query
        self.query_domains = query_domains or []
        self.last_rate_limit_remaining = None
        self.last_rate_limit_reset = None
        SecondProbeFailsRetriever.queries.append(query)

    def search(self, max_results=3):
        if self.query == "rust programming language":
            return []
        return [{"href": "https://example.com", "body": "result"}]


class CliPreflightTests(unittest.IsolatedAsyncioTestCase):
    async def test_preflight_runs_three_probe_queries_and_logs_rate_limits(self):
        SuccessfulProbeRetriever.queries = []
        cfg = SimpleNamespace(retrievers=["brave"])
        sleep_mock = AsyncMock()
        stdout = io.StringIO()

        with patch.object(cli, "get_retriever", return_value=SuccessfulProbeRetriever):
            with patch.object(cli.asyncio, "sleep", sleep_mock):
                with redirect_stdout(stdout):
                    await cli._run_retriever_preflight(cfg)

        self.assertEqual(
            SuccessfulProbeRetriever.queries,
            [
                "test connectivity",
                "rust programming language",
                "python decorators tutorial",
            ],
        )
        self.assertEqual(sleep_mock.await_args_list[0].args[0], 1.5)
        self.assertEqual(sleep_mock.await_args_list[1].args[0], 1.5)
        self.assertIn("rate_limit_remaining=42", stdout.getvalue())

    async def test_preflight_aborts_when_any_probe_returns_zero_results(self):
        SecondProbeFailsRetriever.queries = []
        cfg = SimpleNamespace(retrievers=["brave"])
        sleep_mock = AsyncMock()

        with patch.object(cli, "get_retriever", return_value=SecondProbeFailsRetriever):
            with patch.object(cli.asyncio, "sleep", sleep_mock):
                with patch.object(cli, "_abort_run", side_effect=RuntimeError("abort")):
                    with self.assertRaisesRegex(RuntimeError, "abort"):
                        await cli._run_retriever_preflight(cfg)

        self.assertEqual(
            SecondProbeFailsRetriever.queries,
            ["test connectivity", "rust programming language"],
        )
        self.assertEqual(sleep_mock.await_count, 1)


if __name__ == "__main__":
    unittest.main()
