# Prompt System Reference

## Table of Contents
- [PromptFamily Class](#promptfamily-class)
- [Key Prompt Examples](#key-prompt-examples)

---

## PromptFamily Class

**File:** `gpt_researcher/prompts.py`

All prompts are centralized in the `PromptFamily` class. This allows for model-specific prompt variations.

```python
class PromptFamily:
    """
    General purpose class for prompt formatting.
    Can be overwritten with model-specific derived classes.
    """

    def __init__(self, config: Config):
        self.cfg = config

    @staticmethod
    def get_prompt_by_report_type(report_type: str):
        """Returns the appropriate prompt generator for the report type."""
        match report_type:
            case ReportType.ResearchReport.value:
                return PromptFamily.generate_report_prompt
            case ReportType.DetailedReport.value:
                return PromptFamily.generate_report_prompt
            case ReportType.OutlineReport.value:
                return PromptFamily.generate_outline_report_prompt
            # ... etc
```

---

## Key Prompt Examples

### Agent Selection Prompt

```python
@staticmethod
def generate_agent_role_prompt(query: str, parent_query: str = "") -> str:
    return f"""Analyze the research query and select the most appropriate agent role.

Query: "{query}"
{f'Parent Query: "{parent_query}"' if parent_query else ''}

Based on the query, determine:
1. The domain expertise needed
2. The research approach required
3. The appropriate agent persona

Return a JSON object with:
- "agent": The agent type (e.g., "Research Analyst", "Technical Writer")
- "role": A detailed role description for how the agent should approach this research
"""
```

### Research Planning Prompt

```python
@staticmethod
def generate_search_queries_prompt(
    query: str,
    parent_query: str = "",
    report_type: str = "",
    max_iterations: int = 3,
    context: str = "",
) -> str:
    return f"""Generate {max_iterations} focused search queries to research: "{query}"

Context from initial search:
{context}

Requirements:
- Each query should explore a different aspect
- Queries should be specific and searchable
- Consider the report type: {report_type}

Return a JSON array of query strings.
"""
```

### Report Generation Prompt (with images)

```python
@staticmethod
def generate_report_prompt(
    question: str,
    context: str,
    report_source: str,
    report_format="apa",
    total_words=1000,
    tone=None,
    language="english",
    available_images: list = [],
) -> str:
    # Build image embedding instruction if images available
    image_instruction = ""
    if available_images:
        image_list = "\n".join([
            f"- Title: {img.get('title')}\n  URL: {img['url']}"
            for img in available_images
        ])
        image_instruction = f"""
AVAILABLE IMAGES (embed where relevant):
{image_list}

Use markdown format: ![Title](URL)
"""

    return f"""Information: "{context}"
---
Using the above information, answer: "{question}" in a detailed report.

- Format: {report_format}
- Length: ~{total_words} words
- Tone: {tone.value if tone else "Objective"}
- Language: {language}
- Include citations for all factual claims
{image_instruction}
"""
```

### MCP Tool Selection Prompt

```python
@staticmethod
def generate_mcp_tool_selection_prompt(query: str, tools_info: list, max_tools: int = 3) -> str:
    return f"""Select the most relevant tools for researching: "{query}"

AVAILABLE TOOLS:
{json.dumps(tools_info, indent=2)}

Select exactly {max_tools} tools ranked by relevance.

Return JSON:
{{
  "selected_tools": [
    {{"index": 0, "name": "tool_name", "relevance_score": 9, "reason": "..."}}
  ]
}}
"""
```
