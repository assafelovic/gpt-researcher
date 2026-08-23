"""Regression test: the package must be importable.

gpt_researcher/actions/query_processing.py previously used `Any` in a
function annotation before importing it from `typing`, which crashed the
whole package on import under Python versions without PEP 649/749 lazy
annotation evaluation (i.e. everything before 3.14) -- including the
currently-published 0.16.0 release. See PR #1943.

tests/test_sub_query_normalization.py already exercises this same import
path indirectly (it imports _normalize_sub_queries from this module), but
only as a side effect of testing something else. This makes "the package
imports" an explicit, named invariant instead.
"""

import unittest


class TestPackageImports(unittest.TestCase):
    def test_gpt_researcher_imports(self):
        import gpt_researcher  # noqa: F401

    def test_query_processing_imports(self):
        import gpt_researcher.actions.query_processing  # noqa: F401


if __name__ == "__main__":
    unittest.main()
