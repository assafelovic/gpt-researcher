import os
from unittest.mock import patch

os.environ.setdefault("RETRIEVER_ENDPOINT", "https://example.invalid/search")

from gpt_researcher.retrievers.custom.custom import CustomRetriever

PAYLOAD = [{"url": f"https://example.com/{i}", "raw_content": f"content {i}"} for i in range(10)]


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return PAYLOAD


def _search(max_results):
    retriever = CustomRetriever("anything")
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=FakeResponse()):
        return retriever.search(max_results=max_results)


def test_custom_retriever_honours_max_results():
    results = _search(3)

    assert len(results) == 3
    assert [r["url"] for r in results] == ["https://example.com/0", "https://example.com/1", "https://example.com/2"]


def test_custom_retriever_returns_everything_below_the_limit():
    results = _search(50)

    assert len(results) == len(PAYLOAD)


def test_custom_retriever_keeps_filtering_malformed_rows():
    payload = PAYLOAD[:2] + [{"raw_content": "no url"}, "not-a-dict"]

    retriever = CustomRetriever("anything")
    with patch("gpt_researcher.retrievers.custom.custom.requests.get", return_value=type("R", (), {"raise_for_status": lambda self: None, "json": lambda self: payload})()):
        results = retriever.search(max_results=5)

    assert [r["url"] for r in results] == ["https://example.com/0", "https://example.com/1"]
