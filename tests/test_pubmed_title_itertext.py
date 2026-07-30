"""PubMed title extraction must include nested formatting tags."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

path = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "retrievers"
    / "pubmed_central"
    / "pubmed_central.py"
)
spec = importlib.util.spec_from_file_location("gptr_pubmed_ut", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
PubMedCentralSearch = mod.PubMedCentralSearch

XML = """<?xml version='1.0'?>
<article>
  <front><article-meta>
    <title-group>
      <article-title>Cancer <italic>in vivo</italic> study</article-title>
    </title-group>
  </article-meta></front>
  <abstract><p>Abs</p></abstract>
  <body><p>Body</p></body>
</article>
"""


def test_title_includes_nested_tags():
    s = PubMedCentralSearch("q")
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.text = XML
    with patch.object(mod.requests, "get", return_value=resp):
        out = s._fetch_full_text("PMC1")
    assert out is not None
    assert "in vivo" in out["title"]
    assert out["title"].startswith("Cancer")
