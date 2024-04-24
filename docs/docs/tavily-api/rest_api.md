# Rest API

## Overview

Tavily Search is a robust search API tailored specifically for LLM Agents. It seamlessly integrates with diverse data sources to ensure a superior, relevant search experience.

## Features

* **Curated Results**: Provides top-tier results sorted by relevance across multiple sources.
* **Speed & Efficiency**: Optimized for performance, delivering real-time results.
* **Customizable**: Easily refine search results based on various criteria.
* **Easy Integration**: Simple to integrate with existing applications.

## Base URL

`https://api.tavily.com/`


## Endpoints

### POST `/search`

Search for data based on a query.

#### Parameters
- **api_key** (required): Your unique API key.
- **query** (required): The search query string.
- **search_depth** (optional): The depth of the search. It can be **basic** or **advanced**. Default is **basic** for quick results and **advanced** for indepth high quality results but longer response time. Advanced calls equals 2 requests.
- **include_images** (optional): Include a list of query related images in the response. Default is False.
- **include_answer** (optional): Include answers in the search results. Default is False.
- **include_raw_content** (optional): Include raw content in the search results. Default is False.
- **max_results** (optional): The number of maximum search results to return. Default is 5.
- **include_domains** (optional): A list of domains to specifically include in the search results. Default is None, which includes all domains.
- **exclude_domains** (optional): A list of domains to specifically exclude from the search results. Default is None, which doesn't exclude any domains.

## Example Request

```json
{
  "api_key": "your api key",
  "query": "your search query",
  "search_depth": "basic",
  "include_answer": false,
  "include_images": true,
  "include_raw_content": false,
  "max_results": 5,
  "include_domains": [],
  "exclude_domains": []
}
```

### Response

- **answer**: The answer to your search query.
- **query**: Your search query.
- **response_time**: Your search result response time.
- **images**: A list of query related image urls.
- **follow_up_questions**: A list of suggested research follow up questions related to original query.
- **results**: A list of sorted search results ranked by relevancy. 
  - **title**: The title of the search result url.
  - **url**: The url of the search result.
  - **content**: The most query related content from the scraped url. We use proprietary AI and algorithms to extract only the most relevant content from each url, to optimize for context quality and size.
  - **raw_content**: The parsed and cleaned HTML of the site. For now includes parsed text only.
  - **score**: The relevance score of the search result.

## Example Response

```json
{
    "answer": "Your search result answer",
    "query": "Your search query",
    "response_time": "Your search result response time",
    "follow_up_questions": [
        "follow up question 1",
        "follow up question 2",
        "..."
    ],
    "images": [
      "image url 1",
      "..."
    ]
    "results": [
        {
            "title": "website's title",
            "url": "https://your-search-result-url.com",
            "content": "website's content",
            "raw_content": "website's parsed raw content",
            "score": "tavily's smart relevance score"
        },{},{},{}
    ]
}
```

### Error Codes

- **400**: Bad Request — Your request is invalid.
- **401**: Unauthorized — Your API key is wrong.
- **403**: Forbidden — The endpoint requested is hidden for administrators only.
- **404**: Not Found — The specified endpoint could not be found.
- **405**: Method Not Allowed — You tried to access an endpoint with an invalid method.
- **429**: Too Many Requests — You're requesting too many results! Slow down!
- **500**: Internal Server Error — We had a problem with our server. Try again later.
- **503**: Service Unavailable — We're temporarily offline for maintenance. Please try again later.
- **504**: Gateway Timeout — We're temporarily offline for maintenance. Please try again later.

## Authentication

Tavily Search uses API keys to allow access to the API. You can register a new API key at [https://tavily.com](https://tavily.com).

## Rate Limiting

Tavily Search API has a rate limit of 20 requests per minute.

## Support

For questions, support, or to learn more, please visit [https://tavily.com](https://tavily.com).

