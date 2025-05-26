# ResearchWizard

This is a fork of the [GPT Researcher](https://github.com/assafelovic/gpt_researcher) project.

## What this project is and how it works

**ResearchWizard** is a local-first interface for running `Large Language Models` (LLMs) on your own machine. Think of it like a small-scale, more privacy-conscious alternative to ChatGPT, with a twist—it can make use of various tools, like web search, to enhance its answers. It decides when and how to use these tools based on your input and the context it builds over time. This decision-making process is recursive, meaning it can use tools repeatedly as needed to dig deeper.

### Why choose this over another solution?

Here's what major players like OpenAI are offering to media companies [according to this pitch deck](https://www.adweek.com/media/openai-preferred-publisher-program-deck/):

> Preferred publishers get top placement, “enhanced branding,” and better link visibility inside AI-driven chats.

If you're not into the idea of having your information filtered by those who pay the most, a more transparent, community-driven tool like **ResearchWizard** might be a better fit for you.

### Key Features

* 🕵️‍♀️ Fully local setup (no external APIs needed), making it much more privacy-respecting
* 💸 Runs on affordable, consumer-grade hardware (this demo uses a \~€300 GPU)
* 🤓 Answers include live logs and sources, giving you insight into how results were generated—perfect for deeper exploration
* 🤔 Supports conversational follow-ups naturally
* 📱 Responsive UI that works great on mobile
* 🌓 Light and dark mode included

---

## Roadmap

### What’s currently in progress 👷

#### Persistent Chat / Conversation History 🕵️‍♀️

Still a work-in-progress. Needs major refactoring of internal data handling to support saved chats, with the goal of enabling smoother future expansions without having to redo the architecture.

---

### Coming Soon (Short-Term Plans)

#### User Profiles 🙆

Laying the foundation for private data inside the retrieval pipeline. This could include uploading personal docs or connecting **ResearchWizard** to services like Google Drive or Confluence.

#### Long-Term Memory 🧠

Still exploring how best to handle this. The idea is to let the model learn about the user—preferences, context, etc.—and store persistent info via user-specific namespaces in a vector database.
