# 🌟 Welcome to Tavily 🌟

Welcome to the Tavily Research Platform! In this digital age, quickly accessing relevant and trustworthy information is more crucial than ever. However, we've learned that none of today's search engines provide a suitable tool that provides factual, explicit and objective answers without the need to continuously click and explore multiple sites for a given research task. 

This is why we've built the viral trending open source **[GPT Researcher](https://github.com/assafelovic/gpt-researcher)**. GPT Researcher takes care of the tedious task of research for you, by scraping and aggregating over 20+ web sources per a single research task. 

To build an AI agent that leverages online information is not a simple task. Scraping doesn't scale and requires expertise to refine, current search engine APIs don't provide explicit information to queries but simply potential related articles (which are not always related), and are not very customziable for AI agent needs. This is why we're excited to introduce the first search engine for AI agents - **Tavily Search API**.

Tavily Search API is a search engine optimized for LLMs, paving the way for a seamless, efficient, and persistent search experience. Unlike other search APIs such as Serp or Google, Tavily focuses on optimizing search for AI developers and autonomous AI agents. We take care of all the burden in searching, scraping, filtering and extracting the most relevant information from online sources. All in a single API call! 

To try our API in action, you can now use GPT Researcher on our hosted version [here](https://app.tavily.com/chat) or on our [API Playground](https://app.tavily.com/playground).

If you're an AI developer looking to integrate your application with our API or seek increased API limits, **[please reach out!](mailto:support@tavily.com)**

We're excited to partner with [Langchain](https://blog.langchain.dev/weblangchain/) and [LLamaIndex](https://llamahub.ai/l/tools-tavily) as their recommended search tool! 🚀

## Why Choose Tavily Search API?

1. **Purpose-Built**: Tailored just for LLM Agents, we ensure our features and results resonate with your unique needs. We take care of all the burden in searching, scraping, filtering and extracting information from online sources. All in a single API call!
2. **Versatility**: Beyond just fetching results, Tavily Search API offers precision. With customizable search depths, domain management, and parsing html content controls, you're in the driver's seat.
3. **Performance**: Committed to rapidity and efficiency, our API guarantees real-time outcomes without sidelining accuracy. Please note that we're just getting started, so performance may vary and improve over time.
4. **Integration-friendly**: We appreciate the essence of adaptability. That's why integrating our API with your existing setup is a breeze. You can choose our Python library or a simple API call or any of our supported partners such as [Langchain](https://python.langchain.com/docs/integrations/tools/tavily_search) and [LLamaIndex](https://llamahub.ai/l/tools-tavily).
5. **Transparent & Informative**: Our detailed documentation ensures you're never left in the dark. From setup basics to nuanced features, we've got you covered.

## Getting Started
1. **Sign Up**: Begin by [signing up](https://app.tavily.com) on our platform. It's the first step towards harnessing the power of precision search.
2. **Obtain Your Unique Key**: Once registered, a unique Tavily API key is generated, ensuring you a seamless connection with our services.
3. **Test Drive in the API Playground**: Before diving in, familiarize yourself by testing out endpoints in our interactive [API playground](https://app.tavily.com/playground). Experience firsthand the capabilities we bring to the table.
4. **Explore & Learn**: Dive into our [Python SDK](https://app.tavily.com/documentation/python) or [REST API](https://app.tavily.com/documentation/api) documentation to grasp the depth of our API's prowess. The documentation offers a comprehensive rundown of functionalities, supplemented with practical sample inputs and outputs.
5. **Sample Use - Research Assistant**: Want a real-world application? Check out our [Research Assistant](https://app.tavily.com/chat) — a prime example that showcases how the API can optimize your AI content generation with factual and unbiased results.
6. **Stay Alert**: It's always good to be prepared. Familiarize yourself with our 'Error Codes' to anticipate and troubleshoot potential hiccups. Also, ensure you abide by our guidelines; delve into 'Authentication' and 'Rate Limiting' sections to stay compliant and optimized.

## How does the Search API work?
Current search APIs such as Google, Serp and Bing retrieve search results based on user query. However, the results are sometimes irrelevant to the goal of the search, and return simple site URLs and snippets of content which are not always relevant. In addition, any developer would need to then scrape the sites and retrieve relevant content. This tasks is a burden and requires skills to get right.

Tavily Search API aggregates over 20+ sites per a single API call, and uses propietary AI to score, filter and rank the top most relevant sources and content to your task, query or goal. In addition, Tavily allows developers to add custom fields such as context and limit response tokens to enable the optimal search experience for LLMs.

Remember: Knowledge is power. And with Tavily Search API, you're empowering your LLM with superpowers.

🙋‍♂️ Got questions? Stumbled upon an issue? Or simply intrigued? Don't hesitate! Our support team is always on standby, eager to assist. Join us, dive deep, and redefine your search experience! **[Contact us](mailto:support@tavily.com)**
