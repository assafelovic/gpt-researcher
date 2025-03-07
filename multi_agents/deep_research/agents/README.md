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

## Agent Workflow

The agents work together in the following workflow:

1. `DeepExplorerAgent` generates search queries and a research plan
2. `DeepResearchAgent` conducts basic research on each query
3. `DeepSynthesizerAgent` processes the research results
4. `DeepReviewerAgent` reviews the research quality
5. The process repeats recursively for deeper research levels

## Usage

The agents are orchestrated by the `DeepResearchOrchestrator` class, which creates a LangGraph workflow to coordinate their actions. You don't need to instantiate these agents directly in most cases. 