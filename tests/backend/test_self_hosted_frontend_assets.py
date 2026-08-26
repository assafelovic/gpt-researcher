from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from fastapi.testclient import TestClient

from backend.server.app import app


ASSET_TAG_ATTRIBUTES = {"link": "href", "script": "src"}
EXTERNAL_SCHEMES = {"http", "https"}
ROOT_PATH = "/"


class AssetUrlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.asset_urls: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        asset_attribute = ASSET_TAG_ATTRIBUTES.get(tag)
        if asset_attribute is None:
            return

        attributes = dict(attrs)
        asset_url = attributes.get(asset_attribute)
        if asset_url:
            self.asset_urls.append(asset_url)


def test_self_hosted_frontend_assets_are_same_origin() -> None:
    client = TestClient(app)
    response = client.get(ROOT_PATH)
    response.raise_for_status()

    parser = AssetUrlParser()
    parser.feed(response.text)
    external_assets = [
        asset_url
        for asset_url in parser.asset_urls
        if urlsplit(asset_url).scheme in EXTERNAL_SCHEMES
    ]

    assert external_assets == []
    for asset_url in parser.asset_urls:
        asset_response = client.get(urljoin(ROOT_PATH, asset_url))
        asset_response.raise_for_status()
