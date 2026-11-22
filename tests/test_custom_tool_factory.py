"""Exercise the custom-tool factory through real LangChain schema and invocation APIs."""

import pytest
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from gpt_researcher.utils.tools import create_custom_tool, create_search_tool


def test_factory_preserves_function_parameters_and_metadata():
    def lookup(city: str, units: str = "metric") -> str:
        return f"{city}: {units}"

    lookup_tool = create_custom_tool("weather", "Look up weather", lookup)
    schema = convert_to_openai_tool(lookup_tool)["function"]
    assert schema["name"] == "weather"
    assert schema["description"] == "Look up weather"
    assert set(schema["parameters"]["properties"]) == {"city", "units"}
    assert schema["parameters"]["required"] == ["city"]
    assert lookup_tool.invoke({"city": "杭州"}) == "杭州: metric"
    assert lookup_tool.invoke({"city": "杭州", "units": "imperial"}) == "杭州: imperial"
    with pytest.raises(ValidationError):
        lookup_tool.invoke({})


def test_factory_uses_explicit_parameter_schema():
    def lookup(**kwargs):
        return kwargs["city"]

    lookup_tool = create_custom_tool("weather", "Look up weather", lookup, {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    })
    assert convert_to_openai_tool(lookup_tool)["function"]["parameters"]["required"] == ["city"]
    assert lookup_tool.invoke({"city": "杭州"}) == "杭州"


def test_factory_keeps_none_result_and_error_messages():
    def empty():
        return None

    def fail():
        raise ValueError("invalid input")

    assert create_custom_tool("empty", "Returns no value", empty).invoke({}) == "Tool executed successfully"
    assert create_custom_tool("fail", "Reject invalid input", fail).invoke({}) == (
        "Tool 'fail' received invalid input. Please check the parameters and try again."
    )


def test_existing_search_tool_control():
    search = create_search_tool(lambda query: {"results": [{"title": "Agents", "content": query, "url": "offline"}]})
    assert "Content: research" in search.invoke({"query": "research"})
