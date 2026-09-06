"""SofyaSearch must tolerate malformed payloads and bad config values.

The Sofya API returns a JSON object with a "results" list. Any of those
fields can be missing, null, or the wrong type on an error or empty payload,
and a row whose "title" or "content" is a number would raise out of the
retriever and drop the whole page of results.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from gpt_researcher.retrievers.sofya.sofya import SofyaSearch

ENV = {"SOFYA_API_KEY": "k"}


def _response(payload):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def _call(payload, env=None, **kwargs):
    """Runs a search and returns (results, the mocked requests.post)."""
    max_results = kwargs.pop("max_results", 5)
    with patch.dict(os.environ, {**ENV, **(env or {})}, clear=True):
        retriever = SofyaSearch("q", **kwargs)
        with patch(
            "gpt_researcher.retrievers.sofya.sofya.requests.post",
            return_value=_response(payload),
        ) as post:
            if max_results is None:
                return retriever.search(), post
            return retriever.search(max_results=max_results), post


def test_skips_non_dict_rows_and_missing_urls():
    out, _ = _call(
        {
            "results": [
                {"title": "G", "url": "https://ok.example", "description": "d"},
                "bad",
                None,
                {"title": "n", "description": "d"},
            ]
        }
    )
    assert out == [{"title": "G", "href": "https://ok.example", "body": "d"}]


def test_non_string_fields_do_not_raise():
    out, _ = _call({"results": [{"url": "https://ok.example", "title": 7, "content": 42}]})
    assert out[0]["title"] == "7"
    assert out[0]["raw_content"] == "42"


@pytest.mark.parametrize("payload", [{"results": None}, {"results": "nope"}, [1, 2, 3]])
def test_unusable_payloads_return_empty(payload):
    assert _call(payload)[0] == []


def test_request_error_returns_empty():
    with patch.dict(os.environ, ENV, clear=True):
        retriever = SofyaSearch("q")
        with patch(
            "gpt_researcher.retrievers.sofya.sofya.requests.post",
            side_effect=Exception("boom"),
        ):
            assert retriever.search(max_results=5) == []


def test_basic_depth_passes_the_page_text_through():
    out, post = _call(
        {
            "results": [
                {
                    "url": "https://ok.example",
                    "title": "G",
                    "description": "snippet",
                    "content": "the full page text",
                }
            ]
        }
    )
    assert post.call_args.kwargs["json"]["search_depth"] == "basic"
    assert out[0]["body"] == "snippet"
    assert out[0]["raw_content"] == "the full page text"


def test_snippets_depth_leaves_scraping_to_the_researcher():
    out, post = _call(
        {"results": [{"url": "https://ok.example", "content": "snippet"}]},
        env={"SOFYA_SEARCH_DEPTH": "snippets"},
    )
    assert post.call_args.kwargs["json"]["search_depth"] == "snippets"
    assert "raw_content" not in out[0]


@pytest.mark.parametrize("depth", ["basic", "snippets"])
def test_requires_scraping_tracks_the_depth(depth):
    with patch.dict(os.environ, {**ENV, "SOFYA_SEARCH_DEPTH": depth}, clear=True):
        assert SofyaSearch("q").requires_scraping is (depth != "basic")


def test_unknown_depth_falls_back_to_the_default():
    _, post = _call({"results": []}, env={"SOFYA_SEARCH_DEPTH": "advanced"})
    assert post.call_args.kwargs["json"]["search_depth"] == "basic"


def test_bad_max_results_falls_back_to_the_default():
    _, post = _call({"results": []}, max_results="lots")
    assert post.call_args.kwargs["json"]["max_results"] == 10


def test_max_results_is_clamped_to_the_api_limit():
    _, post = _call({"results": []}, max_results=500)
    assert post.call_args.kwargs["json"]["max_results"] == 20


def test_query_domains_are_reduced_to_host_names():
    _, post = _call(
        {"results": []},
        query_domains=["https://a.example/docs", "b.example", "", "b.example"],
    )
    assert post.call_args.kwargs["json"]["include_domains"] == ["a.example", "b.example"]


def test_missing_api_key_raises():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception):
            SofyaSearch("q")
