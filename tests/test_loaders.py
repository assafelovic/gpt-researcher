from pathlib import Path
import importlib.util

import pytest
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredCSVLoader


FIXTURE_DIR = Path(__file__).parent / "docs"


def test_pymupdf_loader_fixture_loads_pages():
    loader = PyMuPDFLoader(str(FIXTURE_DIR / "doc.pdf"))

    pages = loader.load()

    assert pages
    assert pages[0].metadata["source"].endswith("doc.pdf")


def test_unstructured_csv_loader_fixture_loads_rows():
    if importlib.util.find_spec("pandas") is None:
        pytest.skip("UnstructuredCSVLoader requires pandas, which is not in the base test env")

    loader = UnstructuredCSVLoader(str(FIXTURE_DIR / "sample.csv"), mode="elements")

    rows = loader.load()

    assert rows
    assert any("NCLEX" in row.page_content for row in rows)
