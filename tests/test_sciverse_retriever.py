import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "retrievers" / "sciverse" / "sciverse.py"


def _load():
    requests_mod = types.ModuleType("requests")

    class RequestException(Exception):
        pass

    requests_mod.RequestException = RequestException
    requests_mod.post = MagicMock()
    sys.modules["requests"] = requests_mod
    for key in list(sys.modules):
        if "sciverse.sciverse" in key:
            sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.retrievers.sciverse.sciverse_testmod", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, requests_mod


def _response(payload):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def _route(requests_mod, search_payload, meta_payload=None):
    """Answer /agentic-search and /meta-search with their own fixtures."""

    def post(url, **kwargs):
        if url.endswith("/agentic-search"):
            return _response(search_payload)
        if url.endswith("/meta-search"):
            return _response(meta_payload if meta_payload is not None else {"results": []})
        raise AssertionError(f"unexpected URL: {url}")

    requests_mod.post.side_effect = post


class SciverseRetrieverTests(unittest.TestCase):
    def setUp(self):
        os.environ["SCIVERSE_API_TOKEN"] = "test-token"
        os.environ.pop("SCIVERSE_BASE_URL", None)
        os.environ.pop("SCIVERSE_MODE", None)

    def test_maps_hits_to_title_href_body(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {
                "hits": [
                    {
                        "title": "Attention Is All You Need",
                        "abstract": "We propose the Transformer.",
                        "chunk": "The Transformer uses self-attention.",
                        "doc_id": "sha_a",
                    }
                ]
            },
            {"results": [{"doc_id": "sha_a", "doi": "10.5555/3295222"}]},
        )

        results = mod.SciverseSearch("attention").search(max_results=5)

        self.assertEqual(
            results,
            [
                {
                    "title": "Attention Is All You Need",
                    "href": "https://doi.org/10.5555/3295222",
                    "url": "https://doi.org/10.5555/3295222",
                    "body": "The Transformer uses self-attention.",
                    "raw_content": (
                        "Title: Attention Is All You Need\n\n"
                        "Abstract: We propose the Transformer.\n\n"
                        "Passage from full text: The Transformer uses self-attention."
                    ),
                }
            ],
        )

    def test_link_lookup_batches_doc_ids_in_one_meta_search(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {
                "hits": [
                    {"title": "A", "chunk": "t", "doc_id": "sha_a"},
                    {"title": "B", "chunk": "t", "doc_id": "sha_b"},
                    {"title": "A2", "chunk": "t2", "doc_id": "sha_a"},
                ]
            },
            {"results": []},
        )

        mod.SciverseSearch("q").search()

        meta_calls = [
            c for c in requests_mod.post.call_args_list if c.args[0].endswith("/meta-search")
        ]
        self.assertEqual(len(meta_calls), 1)
        self.assertEqual(
            meta_calls[0].kwargs["json"],
            {
                "filters": [
                    {
                        "field": "doc_id",
                        "operator": "FILTER_OP_IN",
                        "value": ["sha_a", "sha_b"],
                    }
                ],
                "fields": ["doc_id", "access_oa_url", "doi"],
                "page_size": 2,
            },
        )

    def test_sends_auth_and_source_headers_and_maps_mode(self):
        mod, requests_mod = _load()
        _route(requests_mod, {"hits": []})

        mod.SciverseSearch("query", mode="quality").search(max_results=200)

        kwargs = requests_mod.post.call_args.kwargs
        self.assertEqual(kwargs["json"]["top_k"], 100)
        self.assertNotIn("mode", kwargs["json"])
        self.assertEqual(kwargs["json"]["retrieval"], "hybrid")
        self.assertEqual(kwargs["json"]["sub_queries"], 3)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-token")
        self.assertEqual(kwargs["headers"]["X-Sciverse-Source"], "oss_gptresearcher")

    def test_prefers_open_access_url_over_doi(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {"hits": [{"title": "Paper", "chunk": "text", "doc_id": "sha_a"}]},
            {
                "results": [
                    {
                        "doc_id": "sha_a",
                        "access_oa_url": ["https://example.org/paper.pdf"],
                        "doi": "10.1/xyz",
                    }
                ]
            },
        )

        results = mod.SciverseSearch("q").search()

        self.assertEqual(results[0]["href"], "https://example.org/paper.pdf")

    def test_web_hit_without_doc_id_uses_source_url(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {
                "hits": [
                    {
                        "title": "Web page",
                        "chunk": "text",
                        "source_type": "web",
                        "source": "https://example.org/article",
                    }
                ]
            },
        )

        results = mod.SciverseSearch("q").search()

        self.assertEqual(results[0]["href"], "https://example.org/article")

    def test_skips_malformed_hits_and_hits_without_source(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {
                "hits": [
                    "bad",
                    {"title": "No body", "doc_id": "sha_a"},
                    {"title": "No link", "chunk": "text", "source": "s3://bucket/key"},
                    {"title": "Good", "chunk": "text", "doc_id": "sha_b"},
                ]
            },
            {"results": [{"doc_id": "sha_b", "doi": "10.1/b"}]},
        )

        results = mod.SciverseSearch("q").search()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Good")

    def test_link_lookup_failure_degrades_to_web_hrefs_only(self):
        mod, requests_mod = _load()

        def post(url, **kwargs):
            if url.endswith("/agentic-search"):
                return _response(
                    {
                        "hits": [
                            {"title": "Pdf", "chunk": "t", "doc_id": "sha_a"},
                            {
                                "title": "Web",
                                "chunk": "t",
                                "source": "https://example.org/a",
                            },
                        ]
                    }
                )
            raise requests_mod.RequestException("meta-search down")

        requests_mod.post.side_effect = post

        results = mod.SciverseSearch("q").search()

        self.assertEqual([r["title"] for r in results], ["Web"])

    def test_non_dict_payload_returns_empty_list(self):
        mod, requests_mod = _load()
        _route(requests_mod, ["unexpected"])

        self.assertEqual(mod.SciverseSearch("q").search(), [])

    def test_request_error_returns_empty_list(self):
        mod, requests_mod = _load()
        requests_mod.post.side_effect = requests_mod.RequestException("boom")

        self.assertEqual(mod.SciverseSearch("q").search(), [])

    def test_missing_token_raises(self):
        mod, _ = _load()
        os.environ.pop("SCIVERSE_API_TOKEN", None)

        with self.assertRaises(Exception) as ctx:
            mod.SciverseSearch("q")

        self.assertIn("SCIVERSE_API_TOKEN", str(ctx.exception))

    def test_invalid_mode_rejected(self):
        mod, _ = _load()

        with self.assertRaises(AssertionError):
            mod.SciverseSearch("q", mode="turbo")

    def test_mode_env_var_applies_and_invalid_env_falls_back(self):
        mod, requests_mod = _load()
        _route(requests_mod, {"hits": []})

        os.environ["SCIVERSE_MODE"] = "quality"
        mod.SciverseSearch("q").search()
        payload = requests_mod.post.call_args.kwargs["json"]
        self.assertEqual(payload["retrieval"], "hybrid")
        self.assertEqual(payload["sub_queries"], 3)

        # An explicit argument takes precedence over the environment variable
        os.environ["SCIVERSE_MODE"] = "quality"
        mod.SciverseSearch("q", mode="fast").search()
        payload = requests_mod.post.call_args.kwargs["json"]
        self.assertEqual(payload["retrieval"], "es")
        self.assertNotIn("sub_queries", payload)

        # An invalid env value falls back to balanced instead of aborting the research run
        os.environ["SCIVERSE_MODE"] = "turbo"
        mod.SciverseSearch("q").search()
        payload = requests_mod.post.call_args.kwargs["json"]
        self.assertEqual(payload["retrieval"], "hybrid")
        self.assertNotIn("sub_queries", payload)

    def test_raw_content_without_abstract_still_carries_passage(self):
        mod, requests_mod = _load()
        _route(
            requests_mod,
            {"hits": [{"title": "P", "chunk": "some passage", "doc_id": "sha_a"}]},
            {"results": [{"doc_id": "sha_a", "doi": "10.1/x"}]},
        )

        results = mod.SciverseSearch("q").search()

        self.assertEqual(
            results[0]["raw_content"],
            "Title: P\n\nPassage from full text: some passage",
        )


if __name__ == "__main__":
    unittest.main()

    def test_declares_prefetched_content_contract(self):
        # requires_scraping=False: the research flow uses raw_content directly
        # instead of scraping the href (usually a DOI or publisher page), and
        # no longer depends on the legacy 100-char raw_content heuristic.
        mod, _ = _load()
        self.assertIs(mod.SciverseSearch.requires_scraping, False)
