# LangGraph x GPT Researcher
[LangGraph](https://python.langchain.com/docs/langgraph) is a library for building stateful, multi-actor applications with LLMs. 
This example uses Langgraph to automate the process of an in depth research on any given topic.

## Use case
By using Langgraph, the research process can be significantly improved in depth and quality by leveraging multiple agents with specialized skills. 
Inspired by the recent [STORM](https://arxiv.org/abs/2402.14207) paper, this example showcases how a team of AI agents can work together to conduct research on a given topic, from planning to publication.

An average run generates a 5-6 page research report in multiple formats such as PDF, Docx and Markdown.

Please note: Multi-agents are utilizing the same configuration of models like GPT-Researcher does. However, only the SMART_LLM is used for the time being. Please refer to the [LLM config pages](https://docs.gptr.dev/docs/gpt-researcher/llms/llms).

## Research Modes

The system supports two research modes:

### Standard Research
The standard research mode follows a sequential process with a team of agents working together to produce a comprehensive report.

### Deep Research
The deep research mode performs more extensive research by exploring topics in breadth and depth. It allows for:
- Parallel exploration of multiple research queries
- Recursive research to specified depth levels
- Configurable concurrency for performance optimization
- Organized sections with logical headers
- Comprehensive report generation with proper formatting

## The Multi Agent Team
The research team is made up of 8 agents:
- **Human** - The human in the loop that oversees the process and provides feedback to the agents.
- **Chief Editor** - Oversees the research process and manages the team. This is the "master" agent that coordinates the other agents using Langgraph.
- **Researcher** (gpt-researcher) - A specialized autonomous agent that conducts in depth research on a given topic.
- **Editor** - Responsible for planning the research outline and structure.
- **Reviewer** - Validates the correctness of the research results given a set of criteria.
- **Revisor** - Revises the research results based on the feedback from the reviewer.
- **Writer** - Responsible for compiling and writing the final report.
- **Publisher** - Responsible for publishing the final report in various formats.

### Deep Research Agents
For deep research mode, additional specialized agents are used:
- **DeepExplorerAgent** - Generates search queries and research plans
- **DeepSynthesizerAgent** - Processes and synthesizes research results
- **DeepReviewerAgent** - Reviews research quality and completeness
- **SectionWriterAgent** - Organizes research data into logical sections with titles
- **ReportFormatterAgent** - Prepares the final state for the publisher

## How it works
Generally, the process is based on the following stages: 
1. Planning stage
2. Data collection and analysis
3. Review and revision
4. Writing and submission
5. Publication

### Architecture
<div align="center">
<img align="center" height="600" src="https://github.com/user-attachments/assets/ef561295-05f4-40a8-a57d-8178be687b18">
</div>
<br clear="all"/>

### Steps
More specifically (as seen in the architecture diagram) the process is as follows:
- Browser (gpt-researcher) - Browses the internet for initial research based on the given research task.
- Editor - Plans the report outline and structure based on the initial research.
- For each outline topic (in parallel):
  - Researcher (gpt-researcher) - Runs an in depth research on the subtopics and writes a draft.
  - Reviewer - Validates the correctness of the draft given a set of criteria and provides feedback.
  - Revisor - Revises the draft until it is satisfactory based on the reviewer feedback.
- Writer - Compiles and writes the final report including an introduction, conclusion and references section from the given research findings.
- Publisher - Publishes the final report to multi formats such as PDF, Docx, Markdown, etc.

### Deep Research Workflow
The deep research mode follows a different workflow:
1. **DeepExplorerAgent** generates search queries and a research plan
2. Multiple search queries are processed in parallel with a concurrency limit
3. **DeepSynthesizerAgent** processes the research results
4. **DeepReviewerAgent** reviews the research quality
5. The process repeats recursively for deeper research levels
6. **SectionWriterAgent** organizes the research data into logical sections
7. Standard **WriterAgent** creates introduction, conclusion, and table of contents
8. **ReportFormatterAgent** prepares the final state for the publisher
9. Standard **PublisherAgent** creates the final report in the requested formats

## How to run
1. Install required packages found in this root folder including `langgraph`:
    ```bash
    pip install -r requirements.txt
    ```
3. Update env variables, see the [GPT-Researcher docs](https://docs.gptr.dev/docs/gpt-researcher/llms/llms) for more details.

2. Run the application:
    ```bash
    # Run standard research mode
    python main.py --query "Your research question here"
    
    # Run deep research mode
    python main.py --mode deep --query "Your research question" --breadth 4 --depth 2 --concurrency 2
    ```

## Usage
To run research with custom parameters, use the command line arguments:

```bash
# Run standard research
python main.py --mode standard --query "Your research question"

# Run deep research
python main.py --mode deep --query "Your research question" --breadth 4 --depth 2 --concurrency 2 --model "gpt-4o" --verbose
```

### Available Command Line Arguments
- `--mode` - Research mode: "standard" or "deep" (default: "standard")
- `--query` - The research query or task (required)
- `--model` - The OpenAI LLM to use for the agents (default: "gpt-4o")
- `--verbose` - Enable verbose output (default: True)

### Deep Research Arguments
For deep research mode, you can also configure:
- `--breadth` - Number of parallel search queries at each level (default: 4)
- `--depth` - Maximum depth of recursive research (default: 2)
- `--concurrency` - Maximum number of concurrent research tasks (default: 2)
- `--markdown` - Generate markdown output (default: True)
- `--pdf` - Generate PDF output (default: False)
- `--docx` - Generate DOCX output (default: False)

### Example Commands

```bash
# Run standard research on AI
python main.py --mode standard --query "Is AI in a hype cycle?"

# Run deep research with custom parameters
python main.py --mode deep --query "Impact of climate change on agriculture" --breadth 5 --depth 3 --concurrency 3 --pdf --docx
```

The reports will be written in the `outputs` directory.

## To Deploy

```shell
pip install langgraph-cli
langgraph up
```

From there, see documentation [here](https://github.com/langchain-ai/langgraph-example) on how to use the streaming and async endpoints, as well as the playground.
