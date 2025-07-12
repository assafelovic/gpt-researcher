"""Report Analysis Module

This module analyzes user queries to determine report characteristics and requirements.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from gpt_researcher.config import Config
from gpt_researcher.utils.llm import create_chat_completion


async def analyze_query_requirements(
    query: str,
    cfg: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Analyze the user query to determine report requirements and characteristics.

    Args:
        query: The user's research query
        cfg: Configuration object
        cost_callback: Optional cost tracking callback

    Returns:
        Dictionary containing analysis results including:
        - report_style: comparative, analytical, exploratory, etc.
        - user_expertise: beginner, intermediate, expert
        - focus_areas: list of key areas to emphasize
        - enable_debate: whether debate analysis would be beneficial
        - structured_features: which structured research features to enable
    """

    analysis_prompt = f"""
Analyze the following research query to determine the best approach for generating a comprehensive report.

Query: "{query}"

Determine the following characteristics:

1. **Report Style**: What type of analysis would be most valuable?
   - comparative: comparing multiple options/solutions/approaches
   - analytical: deep dive into causes, effects, mechanisms
   - exploratory: broad overview of a new/emerging topic
   - evaluative: assessing pros/cons, effectiveness, quality
   - explanatory: explaining how something works or why it happens
   - investigative: uncovering facts, trends, or hidden information

2. **User Expertise Level**: Based on the query phrasing and complexity:
   - beginner: new to the topic, needs foundational information
   - intermediate: some knowledge, wants deeper insights
   - expert: advanced understanding, seeks cutting-edge information

3. **Key Focus Areas**: What aspects should the report emphasize? (max 4)

4. **Debate Analysis**: Would pro/con debate analysis add value? (true/false)

5. **Structured Features**: Which features would enhance this report?
   - fact_extraction: extract and verify concrete facts
   - quality_control: remove vague language and speculation
   - citation_heavy: emphasize sources and references
   - data_focused: prioritize statistics and quantitative data

Return your analysis as JSON:
{{
    "report_style": "comparative|analytical|exploratory|evaluative|explanatory|investigative",
    "user_expertise": "beginner|intermediate|expert",
    "focus_areas": ["area1", "area2", "area3", "area4"],
    "enable_debate": true|false,
    "structured_features": {{
        "fact_extraction": true|false,
        "quality_control": true|false,
        "citation_heavy": true|false,
        "data_focused": true|false
    }},
    "reasoning": "Brief explanation of the analysis"
}}

Only return valid JSON, no additional text."""

    try:
        response: str = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": "You are an expert research analyst who determines the best approach for research reports."},
                {"role": "user", "content": analysis_prompt}
            ],
            llm_provider=cfg.smart_llm_provider,
            max_tokens=cfg.smart_token_limit,  # pyright: ignore[reportAttributeAccessIssue]
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            cfg=cfg,
        )

        # Parse the JSON response
        analysis: dict[str, Any] = json.loads(response.strip())

        # Validate required fields
        required_fields: list[str] = ["report_style", "user_expertise", "focus_areas", "enable_debate", "structured_features"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing required field: {field}")

        return analysis

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Return sensible defaults if analysis fails
        return {
            "report_style": "analytical",
            "user_expertise": "intermediate",
            "focus_areas": ["overview", "key_findings", "implications", "recommendations"],
            "enable_debate": False,
            "structured_features": {
                "fact_extraction": True,
                "quality_control": True,
                "citation_heavy": True,
                "data_focused": False
            },
            "reasoning": f"Analysis failed ({e.__class__.__name__}), using defaults"
        }

def should_enable_structured_research(analysis: dict[str, Any]) -> bool:
    """Determine if structured research features should be enabled.

    Args:
        analysis: The query analysis results

    Returns:
        True if structured research would benefit this query
    """

    structured_features: dict[str, Any] = analysis.get("structured_features", {})

    # Enable if any structured features are recommended
    return any(structured_features.values())


def get_research_configuration(analysis: dict[str, Any]) -> dict[str, Any]:
    """Get research configuration based on analysis.

    Args:
        analysis: The query analysis results

    Returns:
        Configuration dictionary for research pipeline
    """

    config: dict[str, Any] = {
        "enable_structured_research": should_enable_structured_research(analysis),
        "enable_debate": analysis.get("enable_debate", False),
        "min_confidence": 0.6 if analysis.get("user_expertise") == "expert" else 0.5,
        "max_sections": 10 if analysis.get("report_style") == "analytical" else 8,
        "focus_areas": analysis.get("focus_areas", []),
        "structured_features": analysis.get("structured_features", {}),
    }

    return config
