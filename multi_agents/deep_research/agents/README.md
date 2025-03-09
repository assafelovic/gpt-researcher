# Deep Research Agents

This directory contains the specialized agents used in the deep research process. Each agent has a specific role in the research workflow.

## Agent Structure

- **base.py**: Contains the base `DeepResearchAgent` class and common utilities
  - `count_words()`: Utility function to count words in text
  - `trim_context_to_word_limit()`: Utility to trim context to stay within token limits
  - `ResearchProgress`: Class to track research progress
  - `DeepResearchAgent`: Base agent class with common functionality

- **explorer.py**: Contains the `DeepExplorerAgent` class
  - Responsible for generating search queries and research plans
  - Methods:
    - `generate_search_queries()`: Generates search queries based on the initial query
    - `generate_research_plan()`: Generates follow-up questions to guide research

- **synthesizer.py**: Contains the `DeepSynthesizerAgent` class
  - Responsible for processing and synthesizing research results
  - Methods:
    - `process_research_results()`: Extracts key learnings and follow-up questions from research results

- **reviewer.py**: Contains the `DeepReviewerAgent` class
  - Responsible for reviewing and validating research results
  - Methods:
    - `review_research()`: Evaluates research quality and completeness

- **section_writer.py**: Contains the `SectionWriterAgent` class
  - Responsible for generating structured sections from deep research data
  - Methods:
    - `generate_sections()`: Organizes research data into logical sections with titles
    - `transform_to_research_data()`: Transforms sections into the format expected by the writer agent

- **report_formatter.py**: Contains the `ReportFormatterAgent` class
  - Responsible for formatting the report for the publisher agent
  - Methods:
    - `extract_sections_from_research_data()`: Extracts sections from research data
    - `prepare_publisher_state()`: Prepares the state for the publisher agent

## Agent Workflow

The agents work together in the following workflow:

1. `DeepExplorerAgent` generates search queries and a research plan
2. `DeepResearchAgent` conducts basic research on each query
3. `DeepSynthesizerAgent` processes the research results
4. `DeepReviewerAgent` reviews the research quality
5. The process repeats recursively for deeper research levels
6. `SectionWriterAgent` organizes the research data into logical sections
7. Standard `WriterAgent` creates introduction, conclusion, and table of contents
8. `ReportFormatterAgent` prepares the final state for the publisher
9. Standard `PublisherAgent` creates the final report in the requested formats

## Usage

The agents are orchestrated by the `DeepResearchOrchestrator` class, which creates a LangGraph workflow to coordinate their actions. The research workflow is managed by the orchestrator, while the report generation is handled by the main.py file, which coordinates the SectionWriterAgent, WriterAgent, ReportFormatterAgent, and PublisherAgent. 