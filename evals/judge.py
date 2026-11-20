"""The judge model shared by every eval runner.

An eval run involves two models. The worker model is gpt-researcher itself,
the system under test, configured through its usual SMART_LLM, FAST_LLM and
STRATEGIC_LLM settings. The judge model stands in for a human reviewer: it
grades answers, decides whether a source is trustworthy and whether the
evidence supports a claim, so it should be at least as capable as the worker.

Override the judge per run with the EVAL_JUDGE_MODEL environment variable (or
a line in .env); both models are recorded in each run's log. The name is read
when called, not at import, so a .env loaded by the runner's main() applies.
"""

import os

# A cheap judge for testing and debugging the pipeline. Use a stronger one
# (e.g. gpt-6-sol) for runs whose numbers will be reported.
DEFAULT_JUDGE_MODEL = "gpt-6-luna"

# Reasoning models reject temperature=0 and only run at their default.
_NO_TEMPERATURE_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")


def judge_model_name() -> str:
    return os.getenv("EVAL_JUDGE_MODEL") or DEFAULT_JUDGE_MODEL


def make_judge(model: str | None = None):
    from langchain_openai import ChatOpenAI

    model = model or judge_model_name()
    kwargs = {"model": model, "openai_api_key": os.getenv("OPENAI_API_KEY")}
    if not model.startswith(_NO_TEMPERATURE_PREFIXES):
        kwargs["temperature"] = 0
    return ChatOpenAI(**kwargs)
