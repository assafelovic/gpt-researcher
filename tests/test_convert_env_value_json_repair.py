"""List/dict env coercion should tolerate near-JSON via json_repair."""

import pytest

from gpt_researcher.config.config import Config


def test_list_env_trailing_comma():
    assert Config.convert_env_value("DOMAINS", '["a.com", "b.com",]', list) == [
        "a.com",
        "b.com",
    ]


def test_dict_env_trailing_comma():
    assert Config.convert_env_value("META", '{"k": "v",}', dict) == {"k": "v"}


def test_list_env_rejects_non_list():
    with pytest.raises(ValueError):
        Config.convert_env_value("DOMAINS", '{"not":"a-list"}', list)


def test_dict_env_rejects_non_dict():
    with pytest.raises(ValueError):
        Config.convert_env_value("META", '["not-a-dict"]', dict)


def test_list_env_with_typing_list():
    from typing import List

    assert Config.convert_env_value("DOMAINS", '["a",]', List[str]) == ["a"]
