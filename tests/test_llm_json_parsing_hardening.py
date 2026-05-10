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
