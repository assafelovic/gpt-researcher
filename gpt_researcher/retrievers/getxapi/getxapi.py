"""GetXAPI X/Twitter retriever for GPT Researcher."""

import json
import os
import urllib.parse
import urllib.request


class GetXAPISearch:
    """
    GetXAPI X/Twitter search retriever.

    Searches tweets via the GetXAPI REST API and returns results in the
    standard {title, href, body} format used by all GPT Researcher retrievers.

    Set GETXAPI_API_KEY in your environment. Get one at https://getxapi.com
    """

    def __init__(self, query, query_domains=None, **kwargs):
        self.query = query
        self.query_domains = query_domains
        self.api_key = self.get_api_key()

    def get_api_key(self):
        try:
            api_key = os.environ["GETXAPI_API_KEY"]
        except KeyError:
            raise Exception(
                "GetXAPI API key not found. Please set the GETXAPI_API_KEY "
                "environment variable. Get a key at https://getxapi.com"
            )
        return api_key

    def search(self, max_results=10):
        """
        Search X/Twitter via GetXAPI advanced search.

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
        params = urllib.parse.urlencode({"q": self.query})
        url = f"https://api.getxapi.com/twitter/tweet/advanced_search?{params}"

        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "gpt-researcher/1.0",
        })

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tweets = data.get("tweets") or data.get("data") or []
        search_results = []

        for tweet in tweets[:max_results]:
            author = tweet.get("author") or {}
            username = (
                author.get("userName")
                or author.get("username")
                or author.get("screen_name")
                or tweet.get("username")
                or "unknown"
            )
            text = tweet.get("text") or tweet.get("full_text") or ""
            tweet_id = tweet.get("id") or tweet.get("id_str") or ""

            likes = tweet.get("likeCount") or tweet.get("favorite_count") or 0
            retweets = tweet.get("retweetCount") or tweet.get("retweet_count") or 0
            replies = tweet.get("replyCount") or tweet.get("reply_count") or 0
            views = tweet.get("viewCount") or tweet.get("view_count") or 0

            truncated = text[:80] + ("..." if len(text) > 80 else "")

            search_results.append({
                "title": f"@{username}: {truncated}",
                "href": f"https://x.com/{username}/status/{tweet_id}",
                "body": f"{text}\n\n[likes:{likes} retweets:{retweets} replies:{replies} views:{views}]",
            })

        return search_results
