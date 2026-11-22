"""Redirect targets must be checked before either HTTP client fetches them."""
import asyncio
import importlib.util
import io
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1] / "gpt_researcher"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def modules():
    # Isolate optional scraper/document dependencies, preserving the real HTTP
    # clients and URL guard. Restore sys.modules so other tests remain isolated.
    with patch.dict(sys.modules):
        for name, path in [("gpt_researcher", ROOT),
                           ("gpt_researcher.utils", ROOT / "utils"),
                           ("gpt_researcher.document", ROOT / "document"),
                           ("gpt_researcher.scraper", ROOT / "scraper")]:
            pkg = types.ModuleType(name)
            pkg.__path__ = [str(path)]
            sys.modules[name] = pkg
        security = load_module("gpt_researcher.utils.url_security", "utils/url_security.py")
        for name, attrs in {
            "gpt_researcher.utils.workers": {"WorkerPool": object},
            "gpt_researcher.observability": {"emit_research_event": lambda *a, **k: None},
            "gpt_researcher.document.document": {"detect_utf8": lambda *a: "utf-8"},
            "langchain_community": {},
            "langchain_community.document_loaders": {
                n: object for n in ("PyMuPDFLoader", "TextLoader", "UnstructuredCSVLoader",
                    "UnstructuredExcelLoader", "UnstructuredMarkdownLoader",
                    "UnstructuredPowerPointLoader", "UnstructuredWordDocumentLoader")},
        }.items():
            mod = types.ModuleType(name)
            mod.__dict__.update(attrs)
            sys.modules[name] = mod
        pkg = sys.modules["gpt_researcher.scraper"]
        for name in ("ArxivScraper", "BeautifulSoupScraper", "BrowserScraper", "FireCrawl",
                     "NoDriverScraper", "PyMuPDFScraper", "TavilyExtract", "WebBaseLoaderScraper"):
            setattr(pkg, name, object)
        scraper = load_module("gpt_researcher.scraper.scraper", "scraper/scraper.py")
        document = load_module("gpt_researcher.document.online_document", "document/online_document.py")
        yield security, scraper, document


@pytest.mark.parametrize("target", ["http://127.0.0.1/x", "http://169.254.169.254/x", "file:///etc/passwd"])
def test_requests_rejects_redirect_before_fetch(modules, monkeypatch, target):
    security, scraper, _ = modules
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    hits = []

    def send(adapter, request, **kwargs):
        hits.append(request.url)
        response = requests.Response()
        response.url = request.url
        response.request = request
        response.raw = io.BytesIO(b"")
        response.status_code = 302 if len(hits) == 1 else 200
        response.headers["Location"] = target
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    session = scraper.Scraper([], "test", "bs", None).session
    with pytest.raises(security.UnsafeURLError):
        session.get("http://8.8.8.8/start")
    assert hits == ["http://8.8.8.8/start"]


@pytest.mark.parametrize("target,private", [("http://1.1.1.1/end", False), ("/end", False), ("http://127.0.0.1/end", True)])
def test_requests_allows_valid_redirect(modules, monkeypatch, target, private):
    _, scraper, _ = modules
    monkeypatch.setenv("ALLOW_PRIVATE_URLS", str(private))
    hits = []

    def send(adapter, request, **kwargs):
        hits.append(request.url)
        response = requests.Response()
        response.url, response.request = request.url, request
        response.raw = io.BytesIO(b"")
        response.status_code = 302 if len(hits) == 1 else 200
        response.headers["Location"] = target
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    assert scraper.Scraper([], "test", "bs", None).session.get("http://8.8.8.8/start").status_code == 200
    assert len(hits) == 2


@pytest.mark.parametrize("target,allowed", [("http://169.254.169.254/x", False), ("http://127.0.0.1/x", False), ("file:///etc/passwd", False), ("http://1.1.1.1/end.txt", True), ("/end.txt", True)])
def test_document_redirects(modules, monkeypatch, target, allowed):
    _, _, document = modules
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    hits = []

    class Response:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def read(self):
            return b"document"

    class Session(Response):
        def get(self, url, **kwargs):
            hits.append(url)
            response = Response()
            # Emulate aiohttp's default auto-following behavior on main.
            if kwargs.get("allow_redirects", True) and len(hits) == 1:
                hits.append(target)
            response.status = 302 if len(hits) == 1 else 200
            response.headers = {"Location": target}
            return response

    monkeypatch.setattr(document.aiohttp, "ClientSession", Session)
    loader = document.OnlineDocumentLoader([])

    async def process(path, extension):
        Path(path).unlink()
        return ["loaded"]

    monkeypatch.setattr(loader, "_load_document", process)
    result = asyncio.run(loader._download_and_process("http://8.8.8.8/start.txt"))
    assert result == (["loaded"] if allowed else [])
    assert len(hits) == (2 if allowed else 1)


def test_requests_checks_later_hops(modules, monkeypatch):
    security, scraper, _ = modules
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    hits = []

    def send(adapter, request, **kwargs):
        hits.append(request.url)
        response = requests.Response()
        response.url, response.request = request.url, request
        response.raw = io.BytesIO(b"")
        response.status_code = 302
        response.headers["Location"] = (
            "http://1.1.1.1/next" if len(hits) == 1 else "http://127.0.0.1/secret"
        )
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    with pytest.raises(security.UnsafeURLError):
        scraper.Scraper([], "test", "bs", None).session.get("http://8.8.8.8/start")
    assert hits == ["http://8.8.8.8/start", "http://1.1.1.1/next"]


@pytest.mark.parametrize("loop,private", [(True, False), (False, False), (False, True)])
def test_document_chain_limits_and_private_opt_in(modules, monkeypatch, loop, private):
    _, _, document = modules
    monkeypatch.setenv("ALLOW_PRIVATE_URLS", str(private))
    hits = []

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def get(self, url, **kwargs):
            assert kwargs["allow_redirects"] is False
            hits.append(url)
            self.status = 302 if loop or len(hits) < 3 else 200
            self.headers = {"Location": "/next" if loop or len(hits) == 1 else "http://127.0.0.1/end"}
            return self

        async def read(self):
            return b"body"

    monkeypatch.setattr(document.aiohttp, "ClientSession", Session)
    loader = document.OnlineDocumentLoader([])

    async def process(path, extension):
        Path(path).unlink()
        return ["loaded"]

    monkeypatch.setattr(loader, "_load_document", process)
    result = asyncio.run(loader._download_and_process("http://8.8.8.8/start.txt"))
    assert result == (["loaded"] if private else [])
    assert len(hits) == (6 if loop else 3 if private else 2)
