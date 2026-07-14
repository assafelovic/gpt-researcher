"""Regression tests for Optional[str] env coercion (issue #1899)."""
from typing import Optional, Union

import pytest

from gpt_researcher.config.config import Config


@pytest.mark.parametrize(
    "raw",
    ["none", "null", "", "NONE", "Null"],
)
def test_optional_str_coerces_none_sentinels(raw):
    assert Config.convert_env_value("AGENT_ROLE", raw, Union[str, None]) is None
    assert Config.convert_env_value("AGENT_ROLE", raw, Optional[str]) is None


def test_optional_str_preserves_real_values():
    assert Config.convert_env_value("AGENT_ROLE", "researcher", Optional[str]) == "researcher"
    assert Config.convert_env_value("AGENT_ROLE", "0", Union[str, None]) == "0"


def test_optional_int_still_coerces_and_parses():
    assert Config.convert_env_value("SEED", "none", Optional[int]) is None
    assert Config.convert_env_value("SEED", "42", Optional[int]) == 42
