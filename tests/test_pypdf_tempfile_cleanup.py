"""PDF downloads must close their responses and remove partial files."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from gpt_researcher.scraper.pypdf import pypdf as pdf_module


@pytest.mark.parametrize("failure", ["parse", "download", "http"])
def test_download_resources_removed_on_failure(monkeypatch, tmp_path, failure):
    monkeypatch.setattr(pdf_module.tempfile, "tempdir", str(tmp_path))
    response = MagicMock()

    def body(chunk_size):
        yield b"%PDF-1.4 partial document"
        if failure == "download":
            raise requests.ConnectionError("interrupted download")

    response.iter_content.side_effect = body
    if failure == "http":
        response.raise_for_status.side_effect = requests.HTTPError("HTTP 404")
    session = MagicMock()
    session.get.return_value = response
    loader = MagicMock()
    loader.return_value.load.side_effect = ValueError("corrupt PDF")
    monkeypatch.setattr(pdf_module, "PyPDFLoader", loader)

    assert pdf_module.PyPDFScraper("https://example.com/file.pdf", session).scrape() == ("", [], "")
    response.close.assert_called_once()
    assert list(tmp_path.iterdir()) == []
    if failure == "parse":
        loader.return_value.load.assert_called_once()
        assert not Path(loader.call_args.args[0]).exists()
