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
