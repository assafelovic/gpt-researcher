import json
import unittest
from pathlib import Path

from evals.chinese_reliability.run_benchmark import (
    build_output_documents,
    load_cases,
    run_single_case,
)
from evals.chinese_reliability.source_validator import SourceValidationResult


class FakeResearcher:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def conduct_research(self):
        return ["context"]

    async def write_report(self):
        return "中" * 900

    def get_source_urls(self):
        return ["https://a.example", "https://b.example", "https://c.example"]

    def get_costs(self):
        return 0.03


class FakeValidator:
    async def validate_many(self, urls):
        return [
            SourceValidationResult(
                original_url=url,
                normalized_url=url,
                final_url=url,
                status="valid",
                http_status=200,
                content_length=500,
                reason="ok",
            )
            for url in urls
        ]


class ReliabilityRunnerTests(unittest.IsolatedAsyncioTestCase):
    def test_load_cases_uses_stable_order_and_limit(self):
        path = (
            Path(__file__).parents[1]
            / "evals"
            / "chinese_reliability"
            / "queries.json"
        )

        cases = load_cases(path, limit=1)

        self.assertEqual([case["id"] for case in cases], ["simple-01"])

    def test_load_cases_selects_one_simple_and_one_deep_by_id(self):
        path = (
            Path(__file__).parents[1]
            / "evals"
            / "chinese_reliability"
            / "queries.json"
        )

        cases = load_cases(path, ids=["simple-01", "deep-01"])

        self.assertEqual([case["id"] for case in cases], ["simple-01", "deep-01"])

    async def test_run_single_case_collects_report_sources_and_metrics(self):
        case = {
            "id": "q1",
            "question": "测试问题",
            "report_type": "research_report",
        }

        result = await run_single_case(
            case,
            researcher_factory=FakeResearcher,
            validator=FakeValidator(),
        )

        self.assertEqual(result["id"], "q1")
        self.assertEqual(result["report_type"], "research_report")
        self.assertTrue(result["report_success"])
        self.assertEqual(result["valid_citation_count"], 3)
        self.assertAlmostEqual(result["cost"], 0.03)

    def test_build_output_documents_creates_machine_and_human_readable_content(self):
        runs = [
            {
                "id": "q1",
                "question": "测试问题",
                "report_type": "research_report",
                "report": "报告",
                "error": None,
                "duration_seconds": 1.0,
                "cost": 0.01,
                "citation_count": 3,
                "valid_citation_count": 3,
                "valid_citation_rate": 1.0,
                "report_success": True,
                "source_results": [],
            }
        ]

        documents = build_output_documents(
            runs,
            metadata={"mode": "baseline", "git_commit": "abc", "timestamp": "now"},
        )

        self.assertEqual(documents[Path("reports/q1.md")], "报告")
        self.assertIn(Path("runs.jsonl"), documents)
        self.assertIn(Path("summary.json"), documents)
        self.assertIn(Path("summary.md"), documents)
        summary = json.loads(documents[Path("summary.json")])
        self.assertEqual(summary["summaries"]["research_report"]["total_queries"], 1)


if __name__ == "__main__":
    unittest.main()
