"""Tests for construct_subtopics error handling.

On failure, construct_subtopics returns the original `subtopics` fallback and
logs the error. The log call previously used a non-f-string
("...\\n {e}"), so it recorded the literal text "{e}" instead of the actual
exception, and also printed to stdout. This test pins that the real exception
text is logged.
"""

import logging
import unittest

import pytest

from gpt_researcher.utils.llm import construct_subtopics


class _BrokenConfig:
    """A config stand-in that raises when its attributes are accessed.

    construct_subtopics touches config.smart_llm_model early; raising there
    drives execution into the except branch deterministically.
    """

    def __getattr__(self, name):
        raise RuntimeError("boom-sentinel-12345")


@pytest.mark.asyncio
async def test_construct_subtopics_logs_real_exception(caplog):
    fallback = ["existing-subtopic"]
    with caplog.at_level(logging.ERROR):
        result = await construct_subtopics(
            task="t",
            data="d",
            config=_BrokenConfig(),
            subtopics=fallback,
        )

    # Returns the fallback list rather than crashing.
    assert result == fallback

    # The ACTUAL exception text is logged, not the literal "{e}".
    joined = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "boom-sentinel-12345" in joined
    assert "{e}" not in joined


if __name__ == "__main__":
    unittest.main()
