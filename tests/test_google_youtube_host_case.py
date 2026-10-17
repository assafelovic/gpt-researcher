import json
from unittest.mock import MagicMock, patch

import pytest

from gpt_researcher.retrievers.google.google import GoogleSearch


@pytest.mark.parametrize(
    "youtube_host",
    [
        "youtube.com",
        "YouTube.com",
        "YOUTUBE.COM",
        "www.youtube.com",
        "m.youtube.com",
        "www.YouTube.com:443",
    ],
)
def test_google_search_filters_youtube_host_case_insensitively(youtube_host):
    payload = {
        "items": [
            {
                "title": "Video",
                "link": f"https://{youtube_host}/watch?v=test",
                "snippet": "video result",
            },
            {
                "title": "Article",
                "link": "https://example.com/article",
                "snippet": "article result",
            },
        ]
    }
    response = MagicMock(status_code=200, text=json.dumps(payload))
    search = GoogleSearch(
        "test query",
        headers={
            "google_api_key": "test-key",
            "google_cx_key": "test-cx",
        },
    )

    with patch(
        "gpt_researcher.retrievers.google.google.requests.get",
        return_value=response,
    ):
        result = search.search(max_results=1)

    assert result == [
        {
            "title": "Article",
            "href": "https://example.com/article",
            "body": "article result",
        }
    ]


@pytest.mark.parametrize(
    "link",
    [
        "https://example.com/news/youtube.com",
        "https://example.com/?source=youtube.com",
        "https://example.com/#youtube.com",
        "https://notyoutube.com/article",
        "https://youtube.com.example.org/article",
        "https://youtube.com@example.com/article",
    ],
)
def test_google_search_preserves_non_youtube_hosts(link):
    payload = {
        "items": [{"title": "Article", "link": link, "snippet": "article result"}]
    }
    response = MagicMock(status_code=200, text=json.dumps(payload))
    search = GoogleSearch(
        "test query",
        headers={
            "google_api_key": "test-key",
            "google_cx_key": "test-cx",
        },
    )

    with patch(
        "gpt_researcher.retrievers.google.google.requests.get",
        return_value=response,
    ):
        result = search.search(max_results=1)

    assert result == [
        {"title": "Article", "href": link, "body": "article result"}
    ]
