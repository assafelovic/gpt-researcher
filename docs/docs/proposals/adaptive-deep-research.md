# RFC: Adaptive Deep Research - Quality-Driven Recursive Search

> **Status**: Proposal
> **Author**: Community Contributor
> **Created**: 2026-01-30
> **Target Version**: v4.x

## Summary

This proposal introduces an **Adaptive Deep Research** mode that uses LLM-based quality assessment to dynamically determine search depth, replacing the current fixed-depth recursion approach.

## Motivation

### Current Design Limitations

The existing deep research implementation uses a fixed-depth recursion strategy:

```python
# Current approach
depth = 2  # Fixed value
breadth = 4

# Always executes exactly 2 rounds regardless of query complexity
```

**Problems with this approach:**

| Issue | Description |
|-------|-------------|
| **Resource Waste** | Simple queries still consume 2 full research rounds |
| **Insufficient Depth** | Complex queries may need more than 2 rounds |
| **No Quality Guarantee** | Research stops based on count, not quality |
| **Inflexible** | One-size-fits-all doesn't suit diverse research needs |

### Proposed Solution

Implement a **quality-driven adaptive loop** where an LLM evaluator assesses research quality after each round and decides whether to continue or stop.

```
┌─────────────────────────────────────────────────────────────────┐
│                 Current vs Proposed Design                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CURRENT (Fixed Depth):                                         │
│  ──────────────────────                                         │
│  Search → Search → Stop (always 2 rounds)                       │
│                                                                 │
│  PROPOSED (Adaptive):                                           │
│  ────────────────────                                           │
│  Search → Evaluate → [Quality OK?] → Yes → Stop                 │
│                          │                                      │
│                          └─→ No → Search → Evaluate → ...       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Design

### 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Adaptive Deep Research Flow                     │
└─────────────────────────────────────────────────────────────────┘

                         User Query
                             │
                             ▼
                    ┌────────────────┐
                    │  Research Round │
                    │  (conduct_research)
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Quality Assessor│  ← LLM Evaluation Node
                    │  (assess_quality)│
                    └────────┬───────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌────────────────┐           ┌────────────────┐
     │  Score >= 7/10 │           │  Score < 7/10  │
     │  OR max_depth  │           │  AND has gaps  │
     └────────┬───────┘           └────────┬───────┘
              │                             │
              ▼                             ▼
     ┌────────────────┐           ┌────────────────┐
     │  Generate      │           │  Build Next    │
     │  Final Report  │           │  Query from    │
     │                │           │  Knowledge Gaps│
     └────────────────┘           └────────┬───────┘
                                           │
                                           └──→ (loop back to Research)
```

### 2. Core Components

#### 2.1 AdaptiveDeepResearchSkill Class

```python
# gpt_researcher/skills/adaptive_deep_research.py

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import asyncio
import json

from gpt_researcher.llm_provider import create_chat_completion
from gpt_researcher.config import Config


@dataclass
class QualityAssessment:
    """Quality assessment result from evaluator LLM"""
    score: float                      # Overall score (1-10)
    dimensions: Dict[str, float]      # Individual dimension scores
    reasoning: str                    # Explanation for the score
    has_knowledge_gaps: bool          # Whether gaps exist
    knowledge_gaps: List[str]         # List of identified gaps
    suggested_directions: List[str]   # Suggested research directions


@dataclass
class AdaptiveResearchProgress:
    """Progress tracking for adaptive research"""
    current_depth: int
    quality_score: float
    total_queries: int
    knowledge_gaps_remaining: int
    status: str  # "researching", "evaluating", "completed"


class AdaptiveDeepResearchSkill:
    """
    Adaptive Deep Research Skill

    Uses LLM-based quality assessment to dynamically determine
    when to stop researching, ensuring quality over arbitrary depth.
    """

    def __init__(self, researcher):
        self.researcher = researcher
        self.cfg: Config = researcher.cfg

        # Adaptive parameters
        self.min_depth = 1                    # Minimum research rounds
        self.max_depth = 5                    # Maximum rounds (safety limit)
        self.quality_threshold = 7.0          # Target quality score (1-10)
        self.breadth = 4                      # Queries per round
        self.concurrency_limit = 2            # Parallel query limit

        # Accumulated data
        self.learnings: List[str] = []
        self.context: List[str] = []
        self.citations: Dict[str, str] = {}
        self.visited_urls: Set[str] = set()

        # Progress tracking
        self.current_depth = 0
        self.quality_history: List[QualityAssessment] = []

    async def run(
        self,
        query: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for adaptive deep research.

        Args:
            query: The research question
            on_progress: Optional callback for progress updates

        Returns:
            Dict containing research results, learnings, and metadata
        """
        self.original_query = query

        return await self._adaptive_research_loop(
            query=query,
            on_progress=on_progress
        )

    async def _adaptive_research_loop(
        self,
        query: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Core adaptive research loop with quality-driven termination.
        """

        while self.current_depth < self.max_depth:
            self.current_depth += 1

            # ═══════════════════════════════════════════════════════
            # Step 1: Conduct research round
            # ═══════════════════════════════════════════════════════
            if on_progress:
                on_progress(AdaptiveResearchProgress(
                    current_depth=self.current_depth,
                    quality_score=self._get_latest_score(),
                    total_queries=len(self.learnings),
                    knowledge_gaps_remaining=self._count_gaps(),
                    status="researching"
                ))

            round_results = await self._conduct_research_round(query)

            # Accumulate results
            self.learnings.extend(round_results['learnings'])
            self.context.append(round_results['context'])
            self.citations.update(round_results.get('citations', {}))

            # ═══════════════════════════════════════════════════════
            # Step 2: Quality assessment
            # ═══════════════════════════════════════════════════════
            if on_progress:
                on_progress(AdaptiveResearchProgress(
                    current_depth=self.current_depth,
                    quality_score=self._get_latest_score(),
                    total_queries=len(self.learnings),
                    knowledge_gaps_remaining=self._count_gaps(),
                    status="evaluating"
                ))

            assessment = await self._assess_quality()
            self.quality_history.append(assessment)

            # Log assessment
            await self._log_assessment(assessment)

            # ═══════════════════════════════════════════════════════
            # Step 3: Decision - continue or stop
            # ═══════════════════════════════════════════════════════
            should_stop = self._should_stop_research(assessment)

            if should_stop:
                break

            # Build next query from knowledge gaps
            query = self._build_next_query(assessment)

        # ═══════════════════════════════════════════════════════════
        # Final: Return accumulated results
        # ═══════════════════════════════════════════════════════════
        if on_progress:
            on_progress(AdaptiveResearchProgress(
                current_depth=self.current_depth,
                quality_score=self._get_latest_score(),
                total_queries=len(self.learnings),
                knowledge_gaps_remaining=0,
                status="completed"
            ))

        return {
            'learnings': list(set(self.learnings)),
            'context': '\n\n'.join(self.context),
            'citations': self.citations,
            'visited_urls': self.visited_urls,
            'metadata': {
                'final_depth': self.current_depth,
                'final_quality_score': assessment.score,
                'quality_history': [
                    {'depth': i+1, 'score': a.score}
                    for i, a in enumerate(self.quality_history)
                ],
                'termination_reason': self._get_termination_reason(assessment)
            }
        }

    async def _conduct_research_round(self, query: str) -> Dict[str, Any]:
        """
        Conduct a single research round with multiple queries.
        """
        # Generate search queries for this round
        search_queries = await self._generate_search_queries(query)

        # Execute queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_single_query(sq: Dict) -> Dict:
            async with semaphore:
                return await self._execute_single_research(sq)

        tasks = [process_single_query(sq) for sq in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_learnings = []
        all_context = []
        all_citations = {}

        for result in results:
            if isinstance(result, Exception):
                continue
            all_learnings.extend(result.get('learnings', []))
            all_context.append(result.get('context', ''))
            all_citations.update(result.get('citations', {}))

        return {
            'learnings': all_learnings,
            'context': '\n\n'.join(all_context),
            'citations': all_citations
        }

    async def _assess_quality(self) -> QualityAssessment:
        """
        Use LLM to assess current research quality.

        This is the core evaluation node that determines whether
        the research is sufficient to answer the user's question.
        """

        assessment_prompt = f"""
You are a research quality evaluator. Assess whether the current research
results are sufficient to comprehensively answer the user's question.

## Original Question
{self.original_query}

## Current Research Learnings
{self._format_learnings_for_assessment()}

## Research Context Summary
{self._get_context_summary()}

## Evaluation Dimensions

Please evaluate the research quality on these dimensions (1-10 scale):

1. **Completeness**: Does it cover all key aspects of the question?
2. **Depth**: Is each aspect analyzed with sufficient detail?
3. **Reliability**: Are sources credible? Is there cross-validation?
4. **Actionability**: Does it provide practical, usable insights?

## Output Format (JSON)

{{
    "score": <overall_score_1_to_10>,
    "dimensions": {{
        "completeness": <score>,
        "depth": <score>,
        "reliability": <score>,
        "actionability": <score>
    }},
    "reasoning": "<brief_explanation_for_the_score>",
    "has_knowledge_gaps": <true_or_false>,
    "knowledge_gaps": [
        "<specific_gap_1>",
        "<specific_gap_2>"
    ],
    "suggested_directions": [
        "<suggested_search_direction_1>",
        "<suggested_search_direction_2>"
    ]
}}

Be critical and honest. Only give high scores if the research truly
addresses the question comprehensively.
"""

        response = await create_chat_completion(
            model=self.cfg.strategic_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert research quality assessor. "
                               "Respond only with valid JSON."
                },
                {"role": "user", "content": assessment_prompt}
            ],
            temperature=0.3,
            llm_provider=self.cfg.strategic_llm_provider,
            response_format={"type": "json_object"},
            # Use reasoning model if available
            reasoning_effort="medium" if "o1" in self.cfg.strategic_llm_model or "o3" in self.cfg.strategic_llm_model else None,
        )

        try:
            data = json.loads(response)
            return QualityAssessment(
                score=float(data.get('score', 5)),
                dimensions=data.get('dimensions', {}),
                reasoning=data.get('reasoning', ''),
                has_knowledge_gaps=data.get('has_knowledge_gaps', True),
                knowledge_gaps=data.get('knowledge_gaps', []),
                suggested_directions=data.get('suggested_directions', [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback assessment
            return QualityAssessment(
                score=5.0,
                dimensions={},
                reasoning=f"Assessment parsing failed: {e}",
                has_knowledge_gaps=True,
                knowledge_gaps=["Unable to parse assessment"],
                suggested_directions=["Continue general research"]
            )

    def _should_stop_research(self, assessment: QualityAssessment) -> bool:
        """
        Determine whether to stop researching based on assessment.

        Stop conditions:
        1. Quality score >= threshold
        2. Reached max depth (safety limit)
        3. No more knowledge gaps to explore
        4. Quality not improving (diminishing returns)
        """

        # Condition 1: Quality threshold met
        if assessment.score >= self.quality_threshold:
            return True

        # Condition 2: Max depth reached
        if self.current_depth >= self.max_depth:
            return True

        # Condition 3: No knowledge gaps
        if not assessment.has_knowledge_gaps or not assessment.knowledge_gaps:
            return True

        # Condition 4: Diminishing returns
        if len(self.quality_history) >= 2:
            recent_scores = [a.score for a in self.quality_history[-2:]]
            if recent_scores[-1] - recent_scores[-2] < 0.5:
                # Less than 0.5 improvement, might be diminishing returns
                # But only stop if we've done at least min_depth rounds
                if self.current_depth >= self.min_depth:
                    return True

        return False

    def _build_next_query(self, assessment: QualityAssessment) -> str:
        """
        Build the next research query based on identified gaps.
        """
        gaps = assessment.knowledge_gaps[:3]  # Focus on top 3 gaps
        directions = assessment.suggested_directions[:2]

        return f"""
Original question: {self.original_query}

The current research has identified these knowledge gaps:
{chr(10).join(f'- {gap}' for gap in gaps)}

Suggested research directions:
{chr(10).join(f'- {d}' for d in directions)}

Please conduct focused research to fill these specific gaps.
"""

    # ═══════════════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════════════

    def _format_learnings_for_assessment(self) -> str:
        """Format learnings for the assessment prompt."""
        if not self.learnings:
            return "No learnings collected yet."
        return '\n'.join(f'- {learning}' for learning in self.learnings[-20:])

    def _get_context_summary(self) -> str:
        """Get a summary of research context."""
        full_context = '\n\n'.join(self.context)
        # Truncate to avoid token limits
        return full_context[:4000] + "..." if len(full_context) > 4000 else full_context

    def _get_latest_score(self) -> float:
        """Get the most recent quality score."""
        if not self.quality_history:
            return 0.0
        return self.quality_history[-1].score

    def _count_gaps(self) -> int:
        """Count remaining knowledge gaps."""
        if not self.quality_history:
            return -1  # Unknown
        return len(self.quality_history[-1].knowledge_gaps)

    def _get_termination_reason(self, assessment: QualityAssessment) -> str:
        """Get human-readable termination reason."""
        if assessment.score >= self.quality_threshold:
            return f"Quality threshold met (score: {assessment.score:.1f})"
        if self.current_depth >= self.max_depth:
            return f"Max depth reached ({self.max_depth})"
        if not assessment.has_knowledge_gaps:
            return "No remaining knowledge gaps"
        return "Diminishing returns detected"

    async def _log_assessment(self, assessment: QualityAssessment):
        """Log assessment results."""
        log_msg = (
            f"[Depth {self.current_depth}] "
            f"Quality: {assessment.score:.1f}/10 | "
            f"Gaps: {len(assessment.knowledge_gaps)} | "
            f"Reason: {assessment.reasoning[:100]}..."
        )
        # Use researcher's logging mechanism
        if hasattr(self.researcher, 'websocket') and self.researcher.websocket:
            await self.researcher.websocket.send_json({
                "type": "logs",
                "content": "quality_assessment",
                "output": log_msg
            })
```

#### 2.2 Quality Assessment Prompt Design

The quality assessor uses a multi-dimensional evaluation:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Completeness** | 25% | Coverage of all question aspects |
| **Depth** | 25% | Detail level of analysis |
| **Reliability** | 25% | Source credibility and validation |
| **Actionability** | 25% | Practical value of insights |

#### 2.3 Configuration Options

```python
# Environment variables or config file

# Adaptive mode toggle
DEEP_RESEARCH_MODE = "adaptive"  # "fixed" or "adaptive"

# Quality settings
ADAPTIVE_QUALITY_THRESHOLD = 7      # Score needed to stop (1-10)
ADAPTIVE_MIN_DEPTH = 1              # Minimum rounds
ADAPTIVE_MAX_DEPTH = 5              # Safety limit

# Cost optimization
EVALUATOR_MODEL = "gpt-4o-mini"     # Cheaper model for evaluation
RESEARCH_MODEL = "gpt-4o"           # Stronger model for research

# Diminishing returns detection
MIN_IMPROVEMENT_THRESHOLD = 0.5     # Minimum score improvement to continue
```

### 3. Integration Points

#### 3.1 Modify GPTResearcher

```python
# gpt_researcher/agent.py

class GPTResearcher:
    async def conduct_research(self, on_progress=None):
        if self.report_type == "deep":
            if self.cfg.deep_research_mode == "adaptive":
                # Use new adaptive skill
                skill = AdaptiveDeepResearchSkill(self)
                return await skill.run(self.query, on_progress)
            else:
                # Use existing fixed-depth skill
                skill = DeepResearchSkill(self)
                return await skill.run(on_progress)
```

#### 3.2 WebSocket Progress Updates

```typescript
// Frontend: Handle adaptive progress updates
interface AdaptiveProgress {
  current_depth: number;
  quality_score: number;
  total_queries: number;
  knowledge_gaps_remaining: number;
  status: 'researching' | 'evaluating' | 'completed';
}

// Display quality score in real-time
function handleProgress(progress: AdaptiveProgress) {
  updateUI({
    depth: `Round ${progress.current_depth}`,
    quality: `Quality: ${progress.quality_score.toFixed(1)}/10`,
    status: progress.status,
    gaps: `${progress.knowledge_gaps_remaining} gaps remaining`
  });
}
```

### 4. Example Execution Flows

#### 4.1 Simple Query (Fast Completion)

```
Query: "How to make scrambled eggs?"

Round 1:
  ├─ Research: Basic cooking instructions
  ├─ Quality Assessment: 8.5/10
  │   - Completeness: 9/10 ✓
  │   - Depth: 8/10 ✓
  │   - Reliability: 9/10 ✓
  │   - Actionability: 8/10 ✓
  └─ Decision: STOP (threshold met)

Total: 1 round, ~30 seconds
```

#### 4.2 Complex Query (Deep Exploration)

```
Query: "Impact of quantum computing on cryptocurrency security"

Round 1:
  ├─ Research: General quantum computing + crypto
  ├─ Quality Assessment: 4.0/10
  │   - Gaps: ["Post-quantum cryptography", "Migration timelines"]
  └─ Decision: CONTINUE

Round 2:
  ├─ Research: Post-quantum cryptography algorithms
  ├─ Quality Assessment: 5.5/10
  │   - Gaps: ["Implementation costs", "Industry readiness"]
  └─ Decision: CONTINUE

Round 3:
  ├─ Research: Industry adoption and costs
  ├─ Quality Assessment: 7.2/10
  │   - No critical gaps remaining
  └─ Decision: STOP (threshold met)

Total: 3 rounds, ~3 minutes
```

### 5. Cost Analysis

| Scenario | Fixed (depth=2) | Adaptive | Savings |
|----------|-----------------|----------|---------|
| Simple query | 12 API calls | 4-6 calls | ~50% |
| Medium query | 12 API calls | 8-12 calls | ~0-30% |
| Complex query | 12 API calls | 15-20 calls | -30% (but better quality) |

**Note**: Adaptive mode adds 1 evaluation call per round, but saves multiple research calls for simple queries.

## Implementation Plan

### Phase 1: Core Implementation (Week 1-2)

- [ ] Create `AdaptiveDeepResearchSkill` class
- [ ] Implement quality assessment logic
- [ ] Add configuration options
- [ ] Write unit tests

### Phase 2: Integration (Week 3)

- [ ] Integrate with `GPTResearcher`
- [ ] Add WebSocket progress updates
- [ ] Update frontend to display quality metrics
- [ ] Add CLI support for adaptive mode

### Phase 3: Testing & Optimization (Week 4)

- [ ] Benchmark against fixed-depth mode
- [ ] Tune quality threshold and prompts
- [ ] Add cost tracking and reporting
- [ ] Documentation

### Phase 4: Release (Week 5)

- [ ] Code review
- [ ] Update documentation
- [ ] Release as opt-in feature
- [ ] Gather community feedback

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Infinite loops | High | `max_depth` safety limit |
| Inconsistent evaluation | Medium | Multiple evaluation dimensions, clear rubric |
| Higher costs for complex queries | Low | Cost tracking, user warnings |
| Evaluation latency | Low | Use faster model (gpt-4o-mini) for evaluation |

## Alternatives Considered

1. **Confidence-based stopping**: Use model's confidence instead of quality score
   - Rejected: Confidence doesn't measure research completeness

2. **User-defined depth**: Let users specify depth per query
   - Rejected: Users can't predict optimal depth

3. **Hybrid approach**: Fixed minimum + adaptive extension
   - Partially adopted: `min_depth` ensures baseline coverage

## Success Metrics

- **Efficiency**: 30%+ reduction in API calls for simple queries
- **Quality**: Maintain or improve report quality scores
- **User satisfaction**: Positive feedback on adaptive behavior
- **Cost**: No more than 10% increase in average cost per query

## References

- [Current Deep Research Implementation](../gpt-researcher/gptr/deep_research.md)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## Appendix: Full Code Listing

See the implementation in:
- `gpt_researcher/skills/adaptive_deep_research.py`
- `gpt_researcher/config/config.py` (new config options)
- `frontend/nextjs/components/AdaptiveProgress.tsx`
