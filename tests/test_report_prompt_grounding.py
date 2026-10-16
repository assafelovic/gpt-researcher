"""Regression test: the default report prompt must license per-claim grounding refusal.

The default `generate_report_prompt` demanded a
comprehensive, opinionated report but never told the model what to do when
a source it would otherwise cite doesn't actually support the specific
claim next to its citation -- so the model bridged the gap with plausible
domain knowledge and cited a real, resolvable URL for a claim that source
never made. The prompt's only existing anti-fabrication guard ("Do NOT
cite sources that do not appear in the provided information") forbids
citing an absent source, not misrepresenting a present one.

generate_quick_summary_prompt (a different tool, quick_search) already has
the right shape ("If the results are insufficient to answer the query,
state that clearly.") -- this test asserts generate_report_prompt gained
the equivalent, at the per-claim granularity report synthesis needs.
"""

import unittest

from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.enum import ReportSource


class GenerateReportPromptGroundingTests(unittest.TestCase):
    def test_prompt_licenses_omitting_or_flagging_unsupported_claims(self):
        prompt = PromptFamily.generate_report_prompt(
            question="What is SBVR?",
            context="Source: https://example.com/a\nContent: unrelated text",
            report_source=ReportSource.Web.value,
        )
        lowered = prompt.lower()
        self.assertTrue(
            "does not support" in lowered or "cannot be verified" in lowered,
            f"expected a grounding/refusal guard in the prompt, got:\n{prompt}",
        )

    def test_existing_citation_and_structure_guards_still_present(self):
        # Guard against accidentally dropping the pre-existing guidance
        # while adding the new one.
        prompt = PromptFamily.generate_report_prompt(
            question="q", context="c", report_source=ReportSource.Web.value
        )
        self.assertIn("Do NOT cite sources that do not appear in the provided information", prompt)
        self.assertIn("in-text citation", prompt)


if __name__ == "__main__":
    unittest.main()
