"""The grader model shared by every eval runner.

Override it per run with the EVAL_GRADER_MODEL environment variable (or a
line in .env); the value is recorded in each run's log. The name is read when
called, not at import, so a .env loaded by the runner's main() still applies.
"""

import os

DEFAULT_GRADER_MODEL = "gpt-4-turbo"

# Reasoning models reject temperature=0 and only run at their default.
_NO_TEMPERATURE_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def grader_model_name() -> str:
    return os.getenv("EVAL_GRADER_MODEL") or DEFAULT_GRADER_MODEL


def make_grader(model: str | None = None):
    from langchain_openai import ChatOpenAI

    model = model or grader_model_name()
    kwargs = {"model": model, "openai_api_key": os.getenv("OPENAI_API_KEY")}
    if not model.startswith(_NO_TEMPERATURE_PREFIXES):
        kwargs["temperature"] = 0
    return ChatOpenAI(**kwargs)
