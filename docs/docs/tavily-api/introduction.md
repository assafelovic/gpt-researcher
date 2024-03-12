# Introduction

Tavily Search API is a search engine optimized for LLMs and RAG, aimed at efficient, quick and persistent search results. Unlike other search APIs such as Serp or Google, Tavily focuses on optimizing search for AI developers and autonomous AI agents. We take care of all the burden in searching, scraping, filtering and extracting the most relevant information from online sources. All in a single API call! 

The search API can also be used return answers to questions (for use cases such as multi-agent frameworks like autogen) and can complete comprehensive research tasks in seconds. Moreover, Tavily leverages proprietary financial, code, news, and other data internal data sources to complement online information. 

To try our API in action, you can now use GPT Researcher on our hosted version [here](https://app.tavily.com/chat) or on our [API Playground](https://app.tavily.com/playground).

## Why Choose Tavily Search API?

1. **Purpose-Built**: Tailored just for LLM Agents, we ensure the search results are optimized for [RAG](https://towardsdatascience.com/retrieval-augmented-generation-intuitively-and-exhaustively-explain-6a39d6fe6fc9). We take care of all the burden in searching, scraping, filtering and extracting information from online sources. All in a single API call! Simply pass the returned search results as context to your LLM.
2. **Versatility**: Beyond just fetching results, Tavily Search API offers precision. With customizable search depths, domain management, and parsing html content controls, you're in the driver's seat.
3. **Performance**: Committed to rapidity and efficiency, our API guarantees real-time and trusted information. Please note that we're just getting started, so performance may vary and improve over time.
4. **Integration-friendly**: We appreciate the essence of adaptability. That's why integrating our API with your existing setup is a breeze. You can choose our Python library or a simple API call or any of our supported partners such as [Langchain](https://python.langchain.com/docs/integrations/tools/tavily_search) and [LLamaIndex](https://llamahub.ai/l/tools-tavily).
5. **Transparent & Informative**: Our detailed documentation ensures you're never left in the dark. From setup basics to nuanced features, we've got you covered.

## How does the Search API work?
Current search APIs such as Google, Serp and Bing retrieve search results based on user query. However, the results are sometimes irrelevant to the goal of the search, and return simple site URLs and snippets of content which are not always relevant. Because of this, any developer would need to then scrape the sites for relevant content, filter irrelevant information, optimize the content to fit LLM context limits, and more. This tasks is a burden and requires skills to get right.

Tavily Search API aggregates over 20+ sites per a single API call, and uses proprietary AI to score, filter and rank the top most relevant sources and content to your task, query or goal. 
In addition, Tavily allows developers to add custom fields such as context and limit response tokens to enable the optimal search experience for LLMs.

Tavily can also help your AI agent make better decisions such as suggesting follow up search queries or including a short answer for cross agent communication.

Remember: With LLM hallucinations, it's crucial to optimize for RAG with the right context and information.

## Getting Started
1. **Sign Up**: Begin by [signing up](https://app.tavily.com) on our platform.
2. **Obtain Your Unique Key**: Once registered, a unique Tavily API key is generated, ensuring you a seamless connection with our services.
3. **Test Drive in the API Playground**: Before diving in, familiarize yourself by testing out endpoints in our interactive [API playground](https://app.tavily.com/playground). 
4. **Explore & Learn**: Dive into our [Python SDK](/docs/tavily-api/python-sdk) or [REST API](/docs/tavily-api/rest_api) documentation to get familiar with the various features. The documentation offers a comprehensive rundown of functionalities, supplemented with practical sample inputs and outputs.
5. **Sample Use - Research Assistant**: Want a real-world application? Check out our [Research Assistant](https://app.tavily.com/chat) — a prime example that showcases how the API can optimize your AI content generation with factual and unbiased results.
6. **Stay up to date**: Join our [Community](https://discord.gg/rkYFaa8yHy) to get latest updates on our continuous improvements and development

🙋‍♂️ Got questions? Stumbled upon an issue? Or simply intrigued? Don't hesitate! Our support team is always on standby, eager to assist. Join us, dive deep, and redefine your search experience! **[Contact us](mailto:support@tavily.com)**
