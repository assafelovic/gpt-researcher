# How to Choose

GPT Researcher is a powerful autonomous research agent designed to enhance and streamline your research processes. Whether you're a developer looking to integrate research capabilities into your project or an end-user seeking a comprehensive research solution, GPT Researcher offers flexible options to meet your needs.

We envision a future where AI agents collaborate to complete complex tasks, with research being a critical step in the process. GPT Researcher aims to be your go-to agent for any research task, regardless of complexity. It can be easily integrated into existing agent workflows, eliminating the need to create your own research agent from scratch.

## Options

GPT Researcher offers multiple ways to leverage its capabilities:

<img src="https://github.com/user-attachments/assets/305fa3b9-60fa-42b6-a4b0-84740ab6c665" alt="Logo" width="568"></img>
<br></br>

1. **GPT Researcher PIP agent**: Ideal for integrating GPT Researcher into your existing projects and workflows.
2. **Backend**: A backend service to interact with the frontend user interfaces, offering advanced features like detailed reports.
3. **Multi Agent System**: An advanced setup using LangGraph, offering the most comprehensive research capabilities.
4. **Frontend**: Several front-end solutions depending on your needs, including a simple HTML/JS version and a more advanced NextJS version.

## Usage Options

### 1. PIP Package

The PIP package is ideal for leveraging GPT Researcher as an agent in your preferred environment and code.

**Pros:**
- Easy integration into existing projects
- Flexible usage in multi-agent systems, chains, or workflows
- Optimized for production performance

**Cons:**
- Requires some coding knowledge
- May need additional setup for advanced features

**Installation:**
```
pip install gpt-researcher
```

**System Requirements:**
- Python 3.10+
- pip package manager

**Learn More:** [PIP Documentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

### 2. End-to-End Application

For a complete out-of-the-box experience, including a sleek frontend, you can clone our repository.

**Pros:**
- Ready-to-use frontend and backend services
- Includes advanced use cases like detailed report generation
- Optimal user experience

**Cons:**
- Less flexible than the PIP package for custom integrations
- Requires setting up the entire application

**Getting Started:**
1. Clone the repository: `git clone https://github.com/assafelovic/gpt-researcher.git`
2. Follow the [installation instructions](https://docs.gptr.dev/docs/gpt-researcher/getting-started)

**System Requirements:**
- Git
- Python 3.10+
- Node.js and npm (for frontend)

**Advanced Usage Example:** [Detailed Report Implementation](https://github.com/assafelovic/gpt-researcher/tree/master/backend/report_type/detailed_report)

### 3. Multi Agent System with LangGraph

We've collaborated with LangChain to support multi-agents with LangGraph and GPT Researcher, offering the most complex and comprehensive version of GPT Researcher.

**Pros:**
- Very detailed, customized research reports
- Inner AI agent loops and reasoning

**Cons:**
- More expensive and time-consuming
- Heavyweight for production use

This version is recommended for local, experimental, and educational use. We're working on providing a lighter version soon!

**System Requirements:**
- Python 3.10+
- LangGraph library

**Learn More:** [GPT Researcher x LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)

## Comparison Table

| Feature | PIP Package | End-to-End Application | Multi Agent System |
|---------|-------------|------------------------|---------------------|
| Ease of Integration | High | Medium | Low |
| Customization | High | Medium | High |
| Out-of-the-box UI | No | Yes | No |
| Complexity | Low | Medium | High |
| Best for | Developers | End-users | Researchers/Experimenters |

Please note that all options have been optimized and refined for production use.

## Deep Dive

To learn more about each of the options, check out these docs and code snippets:

1. **PIP Package**: 
   - Install: `pip install gpt-researcher`
   - [Integration guide](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

2. **End-to-End Application**: 
   - Clone the repository: `git clone https://github.com/assafelovic/gpt-researcher.git`
   - [Installation instructions](https://docs.gptr.dev/docs/gpt-researcher/getting-started)

3. **Multi-Agent System**: 
   - [Multi-Agents code](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents)
   - [LangGraph documentation](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)
   - [Blog](https://docs.gptr.dev/blog/gptr-langgraph)

## Versioning and Updates

GPT Researcher is actively maintained and updated. To ensure you're using the latest version:

- For the PIP package: `pip install --upgrade gpt-researcher`
- For the End-to-End Application: Pull the latest changes from the GitHub repository
- For the Multi-Agent System: Check the documentation for compatibility with the latest LangChain and LangGraph versions

## Troubleshooting and FAQs

For common issues and questions, please refer to our [FAQ section](https://docs.gptr.dev/docs/faq) in the documentation.
