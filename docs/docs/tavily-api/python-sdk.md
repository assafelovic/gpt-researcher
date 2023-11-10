
# Python SDK
The [Python library](https://github.com/assafelovic/tavily-python) allows for easy interaction with the Tavily API, offering both basic and advanced search functionalities directly from your Python programs. Easily integrate smart search capabilities into your applications, harnessing Tavily's powerful search features.

## Installing 📦

```bash
pip install tavily-python
```
## Usage 🛠️
The search API has two search depth options: **basic** and **advanced**. The basic search is optimized for performance leading to faster response time. The advanced may take longer (around 5-10 seconds response time) but optimizes for quality. 

Look out for the response **content** field. Using the 'advanced' search depth will highly improve the retrieved content to be only the most related content from each site based on a relevance score. The main search method can be used as seen below:
##
```python
from tavily import TavilyClient
tavily = TavilyClient(api_key="YOUR_API_KEY")
# For basic search:
response = tavily.search(query="Should I invest in Apple in 2024?")
# For advanced search:
response = tavily.search(query="Should I invest in Apple in 2024?", search_depth="advanced")
# Get the search results as context to pass an LLM:
context = [{"url": obj["url"], "content": obj["content"]} for obj in response.results]
```
In addition, you can use other powerful methods based on your application use case as seen below:

```python
# You can easily get search result context based on any max tokens straight into your RAG.
# The response is a string of the context within the max_token limit.
tavily.get_search_context(query="What happened in the burning man floods?", search_depth="advanced", max_tokens=1500)

# You can also get a simple answer to a question including relevant sources all with a simple function call:
tavily.qna_search(query="Where does Messi play right now?")
```

## API Methods 📚

### Client
The Client class is the entry point to interacting with the Tavily API. Kickstart your journey by instantiating it with your API key.

### Methods
* **search**(query, **kwargs)
  * The **search_depth** can be either **basic** or **advanced**. The **basic** type offers a quick response, while the **advanced** type gives in-depth, quality results.
  * Additional parameters can be provided as keyword arguments. See below for a list of all available parameters.
  * Returns a JSON with all related response fields.
* **get_search_context**(query, search_depth [Optional], max_tokens [Optional], **kwargs): 
  * Performs a search and returns a string of content and sources within token limit. 
  * Useful for getting only related content from retrieved websites without having to deal with context extraction and token management.
  * Max tokens defaults to 4,000. Search Depth defaults to basic.
  * Returns a string of the most relevant content including sources that fit within the defined token limit.
* **qna_search**(query, search_depth [Optional], **kwargs): 
  * Performs a search and returns a string containing an answer to the original query including relevant sources
  * Optimal to be used as a tool for AI agents.
  * Search depth defaults to advanced for best answer results.
  * Returns a string of a short answer and related sources.

### Keyword Arguments 🖊️

* **search_depth (str)**: The depth of the search. It can be "basic" or "advanced". Default is "basic" for basic_search and "advanced" for advanced_search.

* **max_results (int)**: The number of maximum search results to return. Default is 5.

* **include_images (bool)**: Include a list of query related images in the response. Default is False.

* **include_answer (bool)**: Include a short answer to original query in the search results. Default is False.

* **include_raw_content (bool)**: Include cleaned and parsed HTML of each site search results. Default is False.

* **include_domains (list)**: A list of domains to specifically include in the search results. Default is None, which includes all domains.

* **exclude_domains (list)**: A list of domains to specifically exclude from the search results. Default is None, which doesn't exclude any domains.

### Response Example
To learn more see [REST API](https://app.tavily.com/documentation/api) documentation.
## Error Handling ⚠️

In case of an unsuccessful HTTP request, a HTTPError will be raised.

## License 📝

This project is licensed under the terms of the MIT license.

## Contact 💌

For questions, support, or to learn more, please visit [Tavily](http://tavily.com) 🌍.

