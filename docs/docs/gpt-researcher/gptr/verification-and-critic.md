# Verification and Reasoning Critic

This fork now adds two review layers to report generation:

1. A verification layer that builds a claim ledger and evidence graph.
2. A reasoning critic that reviews the report against that verification bundle.

The intent is not to guarantee truth. The intent is to make support, uncertainty, and review needs visible by default.

## Verification Review

The verification layer is implemented in:

- `gpt_researcher/actions/verification.py`
- `gpt_researcher/actions/report_generation.py`

It extracts report claims, compares them against the research context, and produces:

- a claim ledger
- an evidence graph
- a support summary
- a risk classification

Risk gating currently focuses on:

- health
- legal
- finance
- security
- politics

When the report touches higher-risk topics, the output is marked for human review.

## Reasoning Critic

The reasoning critic is implemented in:

- `gpt_researcher/actions/reasoning_critic.py`
- `gpt_researcher/actions/report_generation.py`

It reads the report plus the verification bundle and asks a narrower question:

- Are there unsupported claims?
- Are there overconfident statements?
- Are there missing caveats?
- Does the report need manual review?

The critic returns structured JSON and is appended to the report as:

- `## Verification Review`
- `## Reasoning Critic`

If the LLM response is malformed or unavailable, the critic falls back to a deterministic review based on the verification bundle.

## Configuration

The review layers are enabled by default:

- `ENABLE_VERIFICATION_REVIEW`
- `ENABLE_REASONING_CRITIC`

If you want to disable either layer temporarily, set the corresponding flag to `false` in your config or environment.

## What You Will See In A Report

The final report can now include:

- the main synthesis
- a verification appendix
- a critic appendix

The critic appendix typically contains:

- a verdict (`pass`, `revise`, or `high_risk`)
- a confidence score
- strengths
- issues
- recommendations

## Why This Matters

This review stack is especially useful when the research output is being used for:

- technical comparisons
- product decisions
- operational analysis
- sensitive domains where unsupported claims are costly

It does not replace human review for critical topics, but it makes the failure modes much easier to inspect.

## Validation

The review layers are covered by:

- `tests/test_verification.py`
- `tests/test_reasoning_critic.py`

These tests check:

- claim extraction
- evidence graph creation
- risk detection
- critic fallback behavior
- integration into the final report
