"""PubMedCentralSearch reads JATS text as it reads: inline markup inside words, one line per block."""

import xml.etree.ElementTree as ET
from unittest.mock import patch

from gpt_researcher.retrievers.pubmed_central.pubmed_central import (
    PubMedCentralSearch,
    _element_text,
)

ARTICLE = """<pmc-articleset><article><front><article-meta>
<title-group><article-title>Rising CO<sub>2</sub> in <italic>E. coli</italic> cultures</article-title></title-group>
<abstract><sec><title>Background</title><p>H<sub>2</sub>O uptake was measured<xref ref-type="bibr">1</xref>.</p></sec></abstract>
</article-meta></front>
<body><sec><title>Methods</title><p>First paragraph.</p><p>Second paragraph.</p></sec></body>
</article></pmc-articleset>"""


class _Response:
    text = ARTICLE

    def raise_for_status(self):
        return None


def test_fetch_full_text_keeps_words_whole_and_blocks_apart():
    with patch(
        "gpt_researcher.retrievers.pubmed_central.pubmed_central.requests.get",
        return_value=_Response(),
    ):
        result = PubMedCentralSearch("co2")._fetch_full_text("PMC1")

    assert result["title"] == "Rising CO2 in E. coli cultures"
    assert result["body"] == (
        "Title: Rising CO2 in E. coli cultures\n\n"
        "Abstract: Background\nH2O uptake was measured1.\n\n"
        "Body: Methods\nFirst paragraph.\nSecond paragraph."
    )


def test_element_text_handles_missing_and_deeply_nested_elements():
    assert _element_text(None) == ""
    deep = ET.fromstring("<p>" + "<italic>" * 5000 + "x" + "</italic>" * 5000 + "</p>")
    assert _element_text(deep) == "x"
