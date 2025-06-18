# Structured Research Integration

## Overview

The structured research functionality has been integrated into all existing research types in GPT Researcher, replacing the standalone "structured_research" report type. The system now automatically analyzes user queries to determine the appropriate research approach and applies structured research features when beneficial.

## Key Changes

### 1. Simplified Tone Enum

**Before:**

- 16 different tones including analytical categories like "Analytical", "Critical", "Comparative"
- Confusing overlap between tone and report style

**After:**

- 8 personality-focused tones:
  - `Professional` - formal, authoritative, business-appropriate
  - `Conversational` - friendly, approachable, easy to understand  
  - `Academic` - scholarly, rigorous, evidence-based
  - `Journalistic` - investigative, balanced, newsworthy
  - `Technical` - precise, detailed, expert-level
  - `Executive` - concise, strategic, decision-focused
  - `Educational` - clear, instructive, beginner-friendly
  - `Creative` - engaging, storytelling, memorable

### 2. Automatic Query Analysis

New module: `gpt_researcher/actions/report_analyzer.py`

**Features:**

- Analyzes user queries to determine:
  - Report style (comparative, analytical, exploratory, evaluative, explanatory, investigative)
  - User expertise level (beginner, intermediate, expert)
  - Key focus areas
  - Whether debate analysis would be beneficial
  - Which structured research features to enable

**Integration:**

- Runs automatically during `conduct_research()` before agent selection
- Updates tone based on analysis if using default tone
- Configures structured research pipeline based on requirements

### 3. Structured Research Integration

**Core Integration:**

- Structured research pipeline is now initialized automatically when beneficial
- Integrated into the main `GPTResearcher.write_report()` method
- Falls back to regular report generation if structured research fails
- Available in all report types (research_report, detailed_report, etc.)

**Components Integrated:**

- Fact extraction with confidence scoring
- Debate-style analysis (Pro/Con agents with Judge synthesis)
- Fluff classification and content quality control
- Narrative building with citation-backed content

### 4. Removed Standalone Report Type

- Deleted `backend/report_type/structured_research/`
- Removed `StructuredResearch` from `ReportType` enum
- Functionality now available across all report types

## Technical Implementation

### Query Analysis Flow

```python
# 1. Analyze query during conduct_research()
query_analysis = await analyze_query_requirements(query, cfg)
research_config = get_research_configuration(query_analysis)

# 2. Update tone based on analysis
if tone == Tone.Professional:  # Default
    recommended_tone = research_config.get("recommended_tone")
    tone = Tone(recommended_tone)

# 3. Initialize structured pipeline if beneficial
if research_config.get("enable_structured_research"):
    structured_pipeline = StructuredResearchPipeline(llm_provider, cfg)
```

### Report Generation Flow

```python
# 1. Check if structured research is enabled
if structured_pipeline and research_config:
    # 2. Run structured research pipeline
    results = await structured_pipeline.run_structured_research(
        topic=query,
        sources=research_sources,
        enable_debate=research_config.get("enable_debate"),
        min_confidence=research_config.get("min_confidence"),
        max_sections=research_config.get("max_sections"),
    )
    
    # 3. Export as markdown report
    report = structured_pipeline.export_results(results, format="markdown")
    return report
else:
    # 4. Fall back to regular report generation
    return await report_generator.write_report(...)
```

### Tone Mapping

The system automatically maps user expertise and report style to appropriate tones:

```python
tone_mapping = {
    "beginner": {
        "comparative": "Educational",
        "analytical": "Educational", 
        "exploratory": "Conversational",
        # ...
    },
    "intermediate": {
        "comparative": "Professional",
        "analytical": "Professional",
        # ...
    },
    "expert": {
        "comparative": "Technical",
        "analytical": "Academic",
        # ...
    }
}
```

## Benefits

### 1. Automatic Optimization

- No need to manually select structured research
- System determines best approach based on query
- Appropriate tone selection based on user expertise

### 2. Enhanced Quality

- Fact extraction ensures concrete, verifiable information
- Fluff classification removes vague language
- Debate analysis provides balanced perspectives
- Citation-backed narratives improve credibility

### 3. Consistent Experience

- All report types benefit from structured research
- Seamless fallback to regular generation
- Maintains existing API compatibility

### 4. Simplified Configuration

- Fewer tone options reduce confusion
- Automatic feature detection
- Smart defaults based on query analysis

## Usage Examples

### Comparative Analysis

```python
# Query: "Compare Docker vs Podman for enterprise deployment"
# Analysis: report_style="comparative", enable_debate=True
# Result: Pro/Con analysis with Judge synthesis
```

### Beginner-Friendly Explanation  

```python
# Query: "What is machine learning?"
# Analysis: user_expertise="beginner", report_style="explanatory"
# Tone: Educational, structured_features={"fact_extraction": True}
```

### Expert Technical Analysis

```python
# Query: "Latest quantum computing algorithms for optimization"
# Analysis: user_expertise="expert", report_style="investigative" 
# Tone: Academic, min_confidence=0.6, citation_heavy=True
```

## Migration Notes

### For Users

- No breaking changes to existing API
- Structured research now available in all report types
- Tone selection simplified and more intuitive

### For Developers

- `StructuredResearch` report type removed
- New query analysis runs automatically
- Structured research components available via skills module

## Testing

Run the integration test:

```bash
python test_structured_integration.py
```

This verifies:

- Query analysis functionality
- Tone detection and mapping
- Structured research pipeline initialization
- Integration with existing report types
