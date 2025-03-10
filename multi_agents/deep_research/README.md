# Deep Research with LangGraph

This project implements a deep research system using LangGraph, a library for building stateful, multi-actor applications with LLMs. The system can perform in-depth research on a given topic, synthesize the information, and generate comprehensive reports.

## Features

- **Deep Research**: Recursively explore a topic with configurable breadth and depth
- **Stateful Workflow**: Maintain state across multiple research steps using LangGraph's checkpointing
- **Human-in-the-Loop**: Optional human review and feedback during the research process
- **Multi-format Output**: Generate reports in Markdown, PDF, and DOCX formats
- **Customizable Tone**: Adjust the tone of the research output

## Architecture

The system is built using LangGraph's StateGraph to create a workflow with the following components:

1. **Planner**: Generates a research plan with search queries
2. **Explorer**: Executes search queries and collects information
3. **Synthesizer**: Processes and synthesizes the collected information
4. **Reviewer**: Reviews the research and identifies follow-up questions
5. **Finalizer**: Finalizes the research and prepares it for report generation

The workflow is designed to support recursive research, allowing it to explore topics in depth based on the findings at each level.

## State Management

The system uses LangGraph's state management capabilities to maintain and update the research state throughout the workflow. The state includes:

- Research parameters (query, breadth, depth)
- Research progress (current depth, breadth)
- Research results (context items, sources, citations)
- Intermediate results (search queries, follow-up questions)

## Human-in-the-Loop

The system supports human-in-the-loop research through LangGraph's interrupt mechanism. When enabled, the system will pause at review points to allow human feedback and guidance. Humans can:

- Review the current research progress
- Add feedback or additional context
- Suggest follow-up questions
- Continue or stop the research process

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
Create a `.env` file in the root directory with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## Usage

### Command Line

You can run the deep research module directly:

```bash
python -m multi_agents.deep_research.main --query "Your research query" --depth 2 --breadth 4 --human-review
```

Or through the main interface:

```bash
python -m multi_agents.main --mode deep --query "Your research query" --depth 2 --breadth 4 --human-review
```

If you don't provide a query, you'll be prompted to enter one.

### Parameters

- `--mode`: Research mode (default: "deep")
- `--query`: The research query
- `--depth`: Maximum depth of recursive research (default: 2)
- `--breadth`: Number of parallel search queries at each level (default: 4)
- `--concurrency`: Maximum number of concurrent research tasks (default: 2)
- `--source`: Research source ('web' or 'local') (default: 'web')
- `--verbose`: Enable verbose output (default: True)
- `--markdown`: Generate markdown output (default: True)
- `--pdf`: Generate PDF output (default: False)
- `--docx`: Generate DOCX output (default: False)
- `--human-review`: Enable human review during research (default: False)

### Programmatic Usage

```python
from multi_agents.deep_research import run_deep_research

results = await run_deep_research(
    query="Your research query",
    depth=2,
    breadth=4,
    human_review=True
)
```

## Output

The system generates a comprehensive research report that includes:

- Introduction and context
- Detailed findings organized by sections
- Sources and citations
- Conclusion and summary

## Requirements

- Python 3.8+
- LangGraph
- LangChain
- An LLM provider (e.g., OpenAI, Anthropic)

## Troubleshooting

### LangGraph Compatibility Issues

This project is designed to work with LangGraph version 0.0.19. If you encounter import errors, try the following:

1. Install the exact version specified in requirements.txt:
```bash
pip install -r requirements.txt
```

2. If you're still having issues, you can try installing a specific version of LangGraph:
```bash
pip install langgraph==0.0.19
```

3. For newer versions of LangGraph, you might need to update import paths. Common issues include:

   - `append_list` and `merge_dicts` functions: The project includes custom implementations if these are not available in your LangGraph version.
   
   - `MemorySaver` location: This might be in `langgraph.checkpoint.memory` or directly in `langgraph.checkpoint` depending on your version.
   
   - `Command` and `interrupt`: These might be in different modules in different versions.

4. If you're using a very new version of LangGraph, you might need to update the code to use the latest API. Check the [LangGraph documentation](https://python.langchain.com/docs/langgraph) for the latest information.

### Python Version Compatibility

This project is tested with Python 3.8+. If you're using Python 3.12, you might encounter compatibility issues with some dependencies. Try using Python 3.10 or 3.11 if possible.

### API Key Issues

If you're encountering errors related to API calls, make sure your API keys are correctly set in the `.env` file and that you have sufficient credits/quota for the services you're using.

## License

[MIT License](LICENSE) 