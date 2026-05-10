import asyncio

from gpt_researcher.actions.agent_creator import (
    extract_json_with_regex,
    handle_json_error,
)


def test_extract_json_with_regex_strips_code_fences():
    response = """```json
{"server": "🔬 Research Assistant Agent", "agent_role_prompt": "You are a meticulous research assistant AI."}
```"""

    assert extract_json_with_regex(response) == (
        '{"server": "🔬 Research Assistant Agent", "agent_role_prompt": "You are a meticulous research assistant AI."}'
    )


def test_handle_json_error_parses_agent_fields_without_braces():
    response = """```json
server: "🔬 Research Assistant Agent"
agent_role_prompt: "You are a meticulous research assistant AI. Your primary goal is to produce accurate, structured, evidence-based research summaries with clear reasoning and references."
```"""

    result = asyncio.run(handle_json_error(response, "OpenAI API docs"))

    assert result == (
        "🔬 Research Assistant Agent",
        "You are a meticulous research assistant AI. Your primary goal is to produce accurate, structured, evidence-based research summaries with clear reasoning and references.",
    )
