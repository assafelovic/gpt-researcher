# FAQ

### How do I get started?
It really depends on what you're aiming for. 

If you're looking to connect your AI application to the internet with Tavily tailored API, check out the [Tavily API](https://docs.tavily.com/documentation/api-reference/introduction) documentation. 
If you're looking to build and deploy our open source autonomous research agent GPT Researcher, please see [GPT Researcher](/docs/gpt-researcher/getting-started/introduction) documentation.
You can also check out demos and examples for inspiration [here](/docs/examples/examples).

### What is GPT Researcher?

GPT Researcher is a popular open source autonomous research agent that takes care of the tedious task of research for you, by scraping, filtering and aggregating over 20+ web sources per a single research task.

GPT Researcher goes well beyond RAG: it combines planner and execution agents, decision models that keep only the most useful context, multi-agent workflows and recursive deep research, and is optimized for quick and efficient research. It is also fully customizable and can be tailored to your specific needs.

To learn more about GPT Researcher, check out the [documentation page](/docs/gpt-researcher/getting-started/introduction).

### How much does each research run cost?

It depends on the models you configure and the report type. With the default models and settings (measured November 2026), a standard research report costs about \$0.08 and takes about a minute, and a [deep research](/docs/gpt-researcher/gptr/deep_research) run costs about \$1.30 and takes 8–9 minutes. Search API usage (such as Tavily) is billed separately. Every run tracks its own LLM spend, so you can check the exact cost with `researcher.get_costs()` after it finishes. We're constantly optimizing LLM calls to reduce costs and improve performance.

### How do you ensure the report is factual and accurate?

we do our best to ensure that the information we provide is factual and accurate. We do this by using multiple sources, and by using proprietary AI to score and rank the most relevant and accurate information. We also use proprietary AI to filter out irrelevant information and sources.

Lastly, decision models score every scraped passage for how useful it is to the research task and keep only the best ones, leading to more accurate generative AI content and reduced hallucinations.

### What are your plans for the future?

We're constantly working on improving our products and services. We're currently working on improving our search API together with design partners, and adding more data sources to our search engine. We're also working on improving our research agent GPT Researcher, and adding more features to it while growing our amazing open source community.

If you're interested in our roadmap or looking to collaborate, check out our [roadmap page](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap). 

Feel free to [contact us](mailto:assafelovic@gmail.com) if you have any further questions or suggestions!