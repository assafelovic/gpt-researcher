# Xquik X/Twitter Retriever
#
# Searches X (Twitter) for real-time perspectives, dev discussions,
# product feedback, breaking news, and expert opinions.
# $0.00015 per tweet — 33x cheaper than the official X API.

import json
import os
import urllib.parse
import urllib.request


class XquikSearch:
    """
    Xquik X/Twitter search retriever.

    Searches tweets via the Xquik REST API and returns results in the
    standard {title, href, body} format used by all GPT Researcher retrievers.

    Set XQUIK_API_KEY in your environment. Get one at https://xquik.com
    """

    def __init__(self, query, query_domains=None, **kwargs):
        self.query = query
        self.query_domains = query_domains
        self.api_key = self.get_api_key()

    def get_api_key(self):
        try:
            api_key = os.environ["XQUIK_API_KEY"]
        except KeyError:
            raise Exception(
                "Xquik API key not found. Please set the XQUIK_API_KEY "
                "environment variable. Get a key at https://xquik.com"
            )
        return api_key

    def search(self, max_results=10):
        """
        Search X/Twitter via Xquik API.

        Returns:
            list: Search results as [{title, href, body}, ...]
        """
        print(f"Searching X/Twitter with query: {self.query}...")

        try:
            results = self._search_tweets(max_results)
            return results
        except Exception as e:
            print(f"Error: {e}. Failed fetching X/Twitter sources. Resulting in empty response.")
            return []

    def _search_tweets(self, max_results):
        params = urllib.parse.urlencode({
            "q": self.query,
            "limit": min(max_results, 200),
            "queryType": "Top",
        })
        url = f"https://xquik.com/api/v1/x/tweets/search?{params}"

        req = urllib.request.Request(url, headers={
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "gpt-researcher/1.0",
        })

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not isinstance(data, dict):
            return []

        tweets = data.get("tweets") or data.get("data") or []
        if not isinstance(tweets, list):
            return []

        search_results = []

        for tweet in tweets[:max_results]:
            if not isinstance(tweet, dict):
                continue
            author = tweet.get("author") or {}
            if not isinstance(author, dict):
                author = {}
            username = (
                author.get("username")
                or author.get("userName")
                or author.get("screen_name")
                or tweet.get("username")
                or "unknown"
            )
            text = tweet.get("text") or tweet.get("full_text") or ""
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            tweet_id = tweet.get("id") or tweet.get("id_str") or ""
            if not tweet_id:
                continue

            likes = tweet.get("likeCount") or tweet.get("favorite_count") or 0
            retweets = tweet.get("retweetCount") or tweet.get("retweet_count") or 0
            views = tweet.get("viewCount") or tweet.get("view_count") or 0

            engagement = f"{likes} likes, {retweets} RTs"
            if views:
                engagement += f", {views} views"

            title_body = text[:120] + ("..." if len(text) > 120 else "")
            search_results.append({
                "title": f"@{username}: {title_body}",
                "href": f"https://x.com/{username}/status/{tweet_id}",
                "body": f"{text}\n\n[{engagement}]",
            })

        return search_results
