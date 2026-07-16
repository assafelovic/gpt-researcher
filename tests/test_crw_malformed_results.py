"""CRWRetriever must skip non-dict sources."""

from unittest.mock import MagicMock, patch

from gpt_researcher.retrievers.crw.crw import CRWRetriever


def _search(envelope):
    r = CRWRetriever("q", headers={"crw_api_key": "k"})
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = envelope
    with patch("gpt_researcher.retrievers.crw.crw.requests.post", return_value=resp):
        return r.search(max_results=5)


def test_crw_skips_non_dict_sources():
    out = _search(
        {
            "success": True,
            "data": [
                {"url": "https://ok.example", "description": "d"},
                "x",
                {"description": "no url"},
            ],
        }
    )
    assert out == [{"href": "https://ok.example", "body": "d"}]


def test_crw_non_list_data_returns_empty():
    assert _search({"success": True, "data": {"url": "x"}}) == []
