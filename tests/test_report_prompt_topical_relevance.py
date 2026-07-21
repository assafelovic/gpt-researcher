"""Regression test: the default report prompt must exclude topically
irrelevant sources, not just faithfully cite whatever was retrieved.

A source can be faithfully summarized (no hallucination, no fabricated
claim) and still have nothing to do with the query -- e.g. a
software-testing practitioner survey worked into a report about
detecting conflicts between regulatory requirements, presented under an
"Open Research Problems" heading as an accurate paraphrase of that
source's actual content. The prompt's citation guidance governs whether
a cited source appears in the provided context and is faithfully
represented; nothing in it distinguishes "this text is present in the
provided context" from "this text belongs in a report answering this
query."
"""

import unittest

from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.enum import ReportSource


class GenerateReportPromptTopicalRelevanceTests(unittest.TestCase):
    def test_prompt_requires_excluding_topically_irrelevant_sources(self):
        prompt = PromptFamily.generate_report_prompt(
            question="What is SBVR?",
            context="Source: https://example.com/a\nContent: unrelated text",
            report_source=ReportSource.Web.value,
        )
        lowered = prompt.lower()
        self.assertTrue(
            "does not obligate you to use it" in lowered
            or "topically unrelated" in lowered,
            f"expected a topical-relevance exclusion guard in the prompt, got:\n{prompt}",
        )

    def test_existing_citation_guards_still_present(self):
        # Guard against accidentally dropping pre-existing guidance while
        # adding the new topical-relevance guard.
        prompt = PromptFamily.generate_report_prompt(
            question="q", context="c", report_source=ReportSource.Web.value
        )
        self.assertIn("Do NOT cite sources that do not appear in the provided information", prompt)
        self.assertIn("in-text citation", prompt)


if __name__ == "__main__":
    unittest.main()
