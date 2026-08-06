import unittest

from evals.chinese_reliability.metrics import build_run_metrics, summarize_runs
from evals.chinese_reliability.source_validator import SourceValidationResult


def source(url: str, status: str) -> SourceValidationResult:
    return SourceValidationResult(
        original_url=url,
        normalized_url=url,
        final_url=url,
        status=status,
        http_status=200 if status == "valid" else 404,
        content_length=500 if status == "valid" else 0,
        reason="ok" if status == "valid" else "http_404",
    )


class ReliabilityMetricsTests(unittest.TestCase):
    def test_build_run_metrics_calculates_valid_citation_rate_and_success(self):
        metrics = build_run_metrics(
            report="中" * 900,
            source_results=[
                source("https://a.example", "valid"),
                source("https://b.example", "valid"),
                source("https://c.example", "valid"),
                source("https://d.example", "invalid"),
            ],
            duration_seconds=12.5,
            cost=0.02,
        )

        self.assertEqual(metrics["citation_count"], 4)
        self.assertEqual(metrics["valid_citation_count"], 3)
        self.assertAlmostEqual(metrics["valid_citation_rate"], 0.75)
        self.assertTrue(metrics["report_success"])

    def test_build_run_metrics_handles_no_sources_without_division_error(self):
        metrics = build_run_metrics(
            report="中" * 900,
            source_results=[],
            duration_seconds=5,
            cost=None,
        )

        self.assertEqual(metrics["valid_citation_rate"], 0.0)
        self.assertFalse(metrics["report_success"])

    def test_summarize_runs_includes_failures_without_fabricating_cost(self):
        summary = summarize_runs(
            [
                {
                    "error": None,
                    "duration_seconds": 10.0,
                    "cost": 0.1,
                    "citation_count": 4,
                    "valid_citation_count": 3,
                    "report_success": True,
                },
                {
                    "error": "model timeout",
                    "duration_seconds": 20.0,
                    "cost": None,
                    "citation_count": 0,
                    "valid_citation_count": 0,
                    "report_success": False,
                },
            ]
        )

        self.assertEqual(summary["total_queries"], 2)
        self.assertEqual(summary["completed_queries"], 1)
        self.assertAlmostEqual(summary["report_success_rate"], 0.5)
        self.assertAlmostEqual(summary["valid_citation_rate"], 0.75)
        self.assertAlmostEqual(summary["average_duration_seconds"], 10.0)
        self.assertAlmostEqual(summary["average_cost"], 0.1)


if __name__ == "__main__":
    unittest.main()
