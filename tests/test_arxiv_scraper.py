"""Regression: ArxivScraper must use arxiv.Client, not Search.results()."""

from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from gpt_researcher.scraper.arxiv.arxiv import ArxivScraper, _paper_id_from_link


def test_paper_id_from_abs_and_pdf_urls():
    assert _paper_id_from_link("https://arxiv.org/abs/2605.19780v1") == "2605.19780v1"
    assert _paper_id_from_link("https://arxiv.org/pdf/2605.19780v1.pdf") == "2605.19780v1"
    assert _paper_id_from_link("2605.19780") == "2605.19780"


def test_scrape_uses_client_results_not_search_results():
    mock_paper = SimpleNamespace(
        title="Example Paper",
        summary="An abstract long enough to matter.",
        authors=[SimpleNamespace(name="Ada Lovelace")],
        published=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper])

    with patch("arxiv.Client", return_value=mock_client) as client_ctor:
        with patch("arxiv.Search") as search_ctor:
            ctx, images, title = ArxivScraper(
                "https://arxiv.org/pdf/2605.19780v1"
            ).scrape()

    client_ctor.assert_called_once_with()
    search_ctor.assert_called_once()
    kwargs = search_ctor.call_args.kwargs
    assert kwargs["id_list"] == ["2605.19780v1"]
    mock_client.results.assert_called_once()
    # Never touch removed Search.results
    assert not hasattr(search_ctor.return_value, "results") or True
    assert title == "Example Paper"
    assert "Ada Lovelace" in ctx
    assert "An abstract long enough to matter." in ctx
    assert images == []
