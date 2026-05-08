import json
import os
from urllib.request import Request, urlopen

import pytest


BACKEND_URL = os.getenv("GPTR_BACKEND_URL", "http://127.0.0.1:8002")
LLM_URL = os.getenv("GPTR_LLM_URL", "http://127.0.0.1:8081")


def _service_ready(url: str, timeout: float = 2.0) -> bool:
    try:
        with urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


def _require_local_stack():
    if not _service_ready(f"{BACKEND_URL}/api/reports"):
        pytest.skip("Local backend on port 8002 is not available")
    if not _service_ready(f"{LLM_URL}/v1/models"):
        pytest.skip("Local LLM server on port 8081 is not available")


def _post_chat(payload: dict, timeout: float = 20.0) -> dict:
    request = Request(
        f"{BACKEND_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def test_chat_greeting_short_circuits():
    _require_local_stack()

    payload = {"report": "", "messages": [{"role": "user", "content": "hi"}]}
    data = _post_chat(payload, timeout=10.0)

    response = data["response"]
    assert response["content"] == "Hello. What would you like to research?"
    assert response["metadata"] is None


def test_chat_summary_uses_report_only():
    _require_local_stack()

    report = "The backend migrated to port 8002. It removed the stale 8001 process."
    payload = {
        "report": report,
        "messages": [
            {"role": "user", "content": "Summarize this report in one sentence."}
        ],
    }
    data = _post_chat(payload, timeout=10.0)

    response = data["response"]
    assert response["content"] == "According to the report, The backend migrated to port 8002."
    assert response["metadata"] is None


def test_chat_search_returns_live_results():
    _require_local_stack()

    query = "What is the latest news about OpenAI today?"
    payload = {"report": "", "messages": [{"role": "user", "content": query}]}
    data = _post_chat(payload, timeout=30.0)

    response = data["response"]
    assert response["content"].startswith("Here's what I found about What is the latest news about OpenAI today?:")
    assert "Source:" in response["content"]

    metadata = response["metadata"]
    assert metadata is not None
    assert metadata["tool_calls"][0]["tool"] == "quick_search"
    assert metadata["tool_calls"][0]["query"] == query
    assert metadata["tool_calls"][0]["search_metadata"]["query"] == query
    assert metadata["tool_calls"][0]["search_metadata"]["sources"]


def test_chat_report_question_answers_with_report_context():
    _require_local_stack()

    report = "The backend migrated to port 8002. It removed the stale 8001 process."
    payload = {
        "report": report,
        "messages": [{"role": "user", "content": "What port did the backend migrate to?"}],
    }
    data = _post_chat(payload, timeout=15.0)

    response = data["response"]
    assert response["content"] in {
        "The backend migrated to port 8002.",
        "Based on the report, The backend migrated to port 8002.",
    }
    assert response["metadata"] is None
