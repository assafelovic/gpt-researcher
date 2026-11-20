"""Offline regressions for PubMed IDs mapped to PMC full-text IDs."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "retrievers"
    / "pubmed_central"
    / "pubmed_central.py"
)
ARTICLE_XML = """<article>
  <front><article-meta>
    <title-group><article-title>Fixture <italic>in vivo</italic> study</article-title></title-group>
    <abstract><p>Offline abstract.</p></abstract>
  </article-meta></front>
  <body><p>Offline full text.</p></body>
</article>"""


@pytest.fixture
def pubmed_module():
    # Load only this retriever: package imports load unrelated research clients.
    # No private modules or dependency stubs are left in sys.modules.
    spec = importlib.util.spec_from_file_location("_pubmed_mapping_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.dict(
        os.environ,
        {
            "NCBI_API_KEY": "offline-test-key",
            "PUBMED_DB": "pubmed",
            "GPTR_BLOCK_NETWORK": "1",
        },
        clear=True,
    ):
        yield module


def response(*, xml="", data=None):
    result = Mock()
    result.text = xml
    result.json.return_value = data
    return result


def pmc_link(pmid, pmcid):
    return f"""<eLinkResult><LinkSet><IdList><Id>{pmid}</Id></IdList>
      <LinkSetDb><DbTo>pmc</DbTo><LinkName>pubmed_pmc</LinkName>
        <Link><Id>{pmcid}</Id></Link>
      </LinkSetDb>
    </LinkSet></eLinkResult>"""


@pytest.mark.parametrize("xml", [ARTICLE_XML, f"<pmc-articleset>{ARTICLE_XML}</pmc-articleset>"])
def test_pubmed_maps_pmid_before_fetching_full_text(pubmed_module, xml):
    # Official NCBI example: PMID 20466091 corresponds to PMCID PMC2869000.
    # https://pmc.ncbi.nlm.nih.gov/tools/xref-ids/
    search = pubmed_module.PubMedCentralSearch("offline query")
    with patch.object(
        pubmed_module.requests,
        "get",
        side_effect=[
            response(data={"esearchresult": {"idlist": ["20466091"]}}),
            response(xml=pmc_link("20466091", "2869000")),
            response(xml=xml),
        ],
    ) as get:
        results = search.search(max_results=1)

    assert len(results) == 1
    assert results[0]["url"] == results[0]["href"] == (
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2869000/"
    )
    assert "in vivo" in results[0]["title"]
    assert "Offline abstract." in results[0]["raw_content"]
    assert "Offline full text." in results[0]["raw_content"]
    assert get.call_count == 3
    search_call = get.call_args_list[0]
    assert search_call.args[0].endswith("/esearch.fcgi")
    assert search_call.kwargs["params"]["db"] == "pubmed"
    assert search_call.kwargs["timeout"] == 20
    link_call = get.call_args_list[1]
    assert link_call.args[0].endswith("/elink.fcgi")
    assert link_call.kwargs["params"] == {
        "dbfrom": "pubmed",
        "db": "pmc",
        "linkname": "pubmed_pmc",
        "id": "20466091",
        "retmode": "xml",
        "api_key": "offline-test-key",
    }
    assert link_call.kwargs["timeout"] == 20
    fetch_call = get.call_args_list[2]
    assert fetch_call.args[0].endswith("/efetch.fcgi")
    assert fetch_call.kwargs["params"]["db"] == "pmc"
    assert fetch_call.kwargs["params"]["id"] == "2869000"
    assert fetch_call.kwargs["params"]["api_key"] == "offline-test-key"
    assert fetch_call.kwargs["timeout"] == 20


@pytest.mark.parametrize(
    "xml",
    [
        "<eLinkResult><LinkSet><IdList><Id>20466091</Id></IdList></LinkSet></eLinkResult>",
        "<eLinkResult><LinkSetDb><LinkName>pubmed_pubmed</LinkName><Link><Id>123</Id></Link></LinkSetDb></eLinkResult>",
        "<eLinkResult><LinkSetDb><LinkName>pubmed_pmc</LinkName></LinkSetDb></eLinkResult>",
        pmc_link("20466091", "PMC2869000"),
        "<ERROR>No link found</ERROR>",
        "<eLinkResult><ERROR>No link found</ERROR></eLinkResult>",
        "not XML",
    ],
)
def test_pubmed_skips_missing_or_invalid_pmc_links(pubmed_module, xml):
    search = pubmed_module.PubMedCentralSearch("offline query")
    with patch.object(search, "_search_articles", return_value=["20466091"]), patch.object(
        pubmed_module.requests, "get", return_value=response(xml=xml)
    ) as get:
        assert search.search() == []
    assert get.call_count == 1
    assert get.call_args.args[0].endswith("/elink.fcgi")


@pytest.mark.parametrize("failure", [requests.Timeout("offline timeout"), requests.HTTPError("offline HTTP error")])
def test_pubmed_mapping_request_failures_return_empty_list(pubmed_module, failure):
    search = pubmed_module.PubMedCentralSearch("offline query")
    with patch.object(search, "_search_articles", return_value=["20466091"]), patch.object(
        pubmed_module.requests, "get", side_effect=failure
    ) as get:
        assert search.search() == []
    assert get.call_count == 1
    assert get.call_args.args[0].endswith("/elink.fcgi")


def test_pubmed_mapping_http_error_response_is_skipped(pubmed_module):
    search = pubmed_module.PubMedCentralSearch("offline query")
    bad_response = response(xml=pmc_link("20466091", "2869000"))
    bad_response.raise_for_status.side_effect = requests.HTTPError("offline HTTP error")
    with patch.object(search, "_search_articles", return_value=["20466091"]), patch.object(
        pubmed_module.requests, "get", return_value=bad_response
    ) as get:
        assert search.search() == []
    bad_response.raise_for_status.assert_called_once_with()
    assert get.call_count == 1
    assert get.call_args.args[0].endswith("/elink.fcgi")


@pytest.mark.parametrize("middle", ["missing-link", "mapping-error", "fetch-error", "empty-body"])
def test_pubmed_preserves_search_order_and_skips_missing_full_text(pubmed_module, middle):
    search = pubmed_module.PubMedCentralSearch("offline query")
    if middle == "missing-link":
        middle_responses = [response(xml="<eLinkResult><LinkSet/></eLinkResult>")]
    elif middle == "mapping-error":
        middle_responses = [requests.Timeout("offline mapping timeout")]
    elif middle == "fetch-error":
        middle_responses = [response(xml=pmc_link("22", "202")), requests.Timeout("offline fetch timeout")]
    else:
        middle_responses = [response(xml=pmc_link("22", "202")), response(xml="<article><body/></article>")]
    with patch.object(search, "_search_articles", return_value=["11", "22", "33"]), patch.object(
        pubmed_module.requests,
        "get",
        side_effect=[
            response(xml=pmc_link("11", "101")),
            response(xml=ARTICLE_XML.replace("Offline full text.", "First full text.")),
            *middle_responses,
            response(xml=pmc_link("33", "303")),
            response(xml=ARTICLE_XML.replace("Offline full text.", "Last full text.")),
        ],
    ) as get:
        results = search.search()

    assert [item["url"] for item in results] == [
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC101/",
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC303/",
    ]
    expected_ids = ["11", "101", "22"]
    if middle in ("fetch-error", "empty-body"):
        expected_ids.append("202")
    assert [call.kwargs["params"]["id"] for call in get.call_args_list] == expected_ids + ["33", "303"]


@pytest.mark.parametrize("article_id", ["2869000", "PMC2869000"])
def test_default_pmc_fetch_and_citation_remain_unchanged(pubmed_module, article_id):
    os.environ.pop("PUBMED_DB")
    search = pubmed_module.PubMedCentralSearch("offline query")
    assert search.db_type == "pmc"
    with patch.object(search, "_search_articles", return_value=[article_id]), patch.object(
        pubmed_module.requests, "get", return_value=response(xml=ARTICLE_XML)
    ) as get:
        results = search.search()
    assert get.call_count == 1
    assert get.call_args.args[0].endswith("/efetch.fcgi")
    assert get.call_args.kwargs["params"]["id"] == article_id
    assert results[0]["url"] == f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article_id}/"


@pytest.mark.parametrize(
    "xml",
    [
        "<ERROR>Failed to retrieve document</ERROR>",
        f"<pmc-articleset><ERROR>Failed to retrieve document</ERROR>{ARTICLE_XML}</pmc-articleset>",
        "<response><article-title>Metadata only</article-title><body>Not an article</body></response>",
        "<article><article-title>Metadata only</article-title></article>",
        "<article><body/></article>",
        "<article><body>  <p> </p>  </body></article>",
        "not XML",
    ],
)
def test_full_text_errors_and_empty_bodies_are_not_articles(pubmed_module, xml):
    os.environ["PUBMED_DB"] = "pmc"
    search = pubmed_module.PubMedCentralSearch("offline query")
    with patch.object(pubmed_module.requests, "get", return_value=response(xml=xml)):
        assert search._fetch_full_text("2869000") is None


def test_pubmed_full_text_http_error_is_skipped(pubmed_module):
    search = pubmed_module.PubMedCentralSearch("offline query")
    bad_response = response(xml=ARTICLE_XML)
    bad_response.raise_for_status.side_effect = requests.HTTPError("offline HTTP error")
    with patch.object(search, "_search_articles", return_value=["20466091"]), patch.object(
        pubmed_module.requests,
        "get",
        side_effect=[response(xml=pmc_link("20466091", "2869000")), bad_response],
    ) as get:
        assert search.search() == []
    assert get.call_count == 2
