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


@pytest.mark.parametrize(
    ("link", "paper_id"),
    [
        ("https://arxiv.org/pdf/2605.19780v1", "2605.19780v1"),
        ("https://arxiv.org/abs/hep-th/9901001v2", "hep-th/9901001v2"),
        ("https://arxiv.org/pdf/math.GT/0309136v1.pdf", "math.GT/0309136v1"),
        ("https://arxiv.org/abs/math.GT/0309136", "math.GT/0309136"),
        ("math.GT/0309136v2", "math.GT/0309136v2"),
    ],
)
def test_scrape_uses_client_results_not_search_results(link, paper_id):
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
            ctx, images, title = ArxivScraper(link).scrape()

    client_ctor.assert_called_once_with()
    search_ctor.assert_called_once()
    kwargs = search_ctor.call_args.kwargs
    assert kwargs["id_list"] == [paper_id]
    mock_client.results.assert_called_once()
    assert title == "Example Paper"
    assert "Ada Lovelace" in ctx
    assert "An abstract long enough to matter." in ctx
    assert images == []
