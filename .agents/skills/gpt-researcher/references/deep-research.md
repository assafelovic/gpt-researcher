# Deep Research Mode Reference

## Table of Contents
- [Overview](#overview)
- [Configuration](#configuration)
- [DeepResearchSkill](#deepresearchskill)
- [Usage](#usage)

---

## Overview

Deep Research uses recursive tree-like exploration with configurable depth and breadth.

---

## Configuration

```bash
DEEP_RESEARCH_BREADTH=4    # Subtopics per level
DEEP_RESEARCH_DEPTH=2      # Recursion levels
DEEP_RESEARCH_CONCURRENCY=2  # Parallel tasks
```

---

## DeepResearchSkill

**File:** `gpt_researcher/skills/deep_research.py`

```python
class DeepResearchSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.breadth = getattr(researcher.cfg, 'deep_research_breadth', 4)
        self.depth = getattr(researcher.cfg, 'deep_research_depth', 2)
        self.concurrency_limit = getattr(researcher.cfg, 'deep_research_concurrency', 2)
        self.learnings = []
        self.research_sources = []
        self.context = []

    async def deep_research(self, query: str, on_progress=None) -> str:
        """
        Recursive research with depth and breadth.
        
        1. Research main topic
        2. Generate subtopics (breadth)
        3. For each subtopic, recursively research (depth)
        4. Aggregate all findings
        5. Generate comprehensive report
        """
```

---

## Usage

```python
researcher = GPTResearcher(
    query="Comprehensive analysis of quantum computing",
    report_type="deep",  # Triggers deep research
)
await researcher.conduct_research()
report = await researcher.write_report()
```

### Research Tree Structure

```
Query: "Quantum Computing"
├── Subtopic 1: Hardware (depth 1)
│   ├── Subtopic 1.1: Superconducting qubits (depth 2)
│   └── Subtopic 1.2: Ion traps (depth 2)
├── Subtopic 2: Algorithms (depth 1)
│   ├── Subtopic 2.1: Shor's algorithm (depth 2)
│   └── Subtopic 2.2: Grover's algorithm (depth 2)
├── Subtopic 3: Applications (depth 1)
│   └── ...
└── Subtopic 4: Challenges (depth 1)
    └── ...
```

With `DEEP_RESEARCH_BREADTH=4` and `DEEP_RESEARCH_DEPTH=2`, this explores 4 subtopics at each level, going 2 levels deep.
