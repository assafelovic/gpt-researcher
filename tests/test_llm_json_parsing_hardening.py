from gpt_researcher.utils.json_parsing import parse_llm_json_response


def test_parse_llm_json_response_handles_code_fenced_object_without_braces():
    response = """```json
verdict: revise
confidence: 0.83
summary: One comparative claim is a little too strong.
issues: []
strengths: ["The report includes a verification appendix."]
recommendations: ["Soften absolute performance language."]
```"""

    payload = parse_llm_json_response(response, expected_kind="object")

    assert isinstance(payload, dict)
    assert payload["verdict"] == "revise"
    assert payload["confidence"] == 0.83
    assert payload["issues"] == []


def test_parse_llm_json_response_handles_code_fenced_array():
    response = """```json
"OpenAI API docs", "OpenAI Python API library", "OpenAI API Platform Documentation"
```"""

    payload = parse_llm_json_response(response, expected_kind="array")

    assert payload == [
        "OpenAI API docs",
        "OpenAI Python API library",
        "OpenAI API Platform Documentation",
    ]


def test_parse_llm_json_response_strips_ansi_wrapped_code_fences():
    response = "\x1b[32m```json\n\x1b[0mbuce: \"no brand touchpoints or extras, no extras added\"\n\x1b[32m```\x1b[0m"

    payload = parse_llm_json_response(response, expected_kind="object")

    assert isinstance(payload, dict)
    assert payload["buce"] == "no brand touchpoints or extras, no extras added"
