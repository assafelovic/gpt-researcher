"""Regression tests for extract_json_with_regex (agent JSON recovery).

The helper used a non-greedy ``{.*?}`` pattern, which stopped at the FIRST
closing brace. That truncated any JSON object that had more than one key or
a ``}`` inside a string value (e.g. an agent_role_prompt mentioning
"{markets}"), producing an invalid fragment that json.loads could not parse.
A greedy ``{.*}`` spans to the last ``}`` and captures the whole object.
"""

import json

from gpt_researcher.actions.agent_creator import extract_json_with_regex


def test_multi_key_object_not_truncated():
    response = 'prefix {"server": "A", "agent_role_prompt": "B"} suffix'
    extracted = extract_json_with_regex(response)
    assert json.loads(extracted) == {"server": "A", "agent_role_prompt": "B"}


def test_brace_inside_string_value_preserved():
    response = (
        'Here is the agent: '
        '{"server": "Finance", "agent_role_prompt": "analyze {markets} data"} done'
    )
    extracted = extract_json_with_regex(response)
    parsed = json.loads(extracted)
    assert parsed["server"] == "Finance"
    assert parsed["agent_role_prompt"] == "analyze {markets} data"


def test_none_input_returns_none():
    assert extract_json_with_regex(None) is None


def test_no_json_returns_none():
    assert extract_json_with_regex("no object here") is None
