import json
import os
from typing import Any, Optional

import tiktoken

# Default encoding fallback (works for many modern OpenAI models)
ENCODING_MODEL = "o200k_base"

# Fallback (legacy) per-token cost estimation when model pricing is not configured.
# NOTE: This is intentionally kept for backwards compatibility; for accurate costs,
# configure MODEL_PRICING_JSON / MODEL_PRICING_PER_1M_JSON.
INPUT_COST_PER_TOKEN = 0.000005
OUTPUT_COST_PER_TOKEN = 0.000015

IMAGE_INFERENCE_COST = 0.003825
EMBEDDING_COST = 0.02 / 1000000  # Assumes new ada-3-small


def _get_encoding(model: str | None):
    if model:
        try:
            return tiktoken.encoding_for_model(model)
        except Exception:
            pass
    return tiktoken.get_encoding(ENCODING_MODEL)


def _load_model_pricing_per_1m() -> dict[str, dict[str, float]]:
    """
    Load model pricing config from environment.

    Supported env vars:
    - MODEL_PRICING_PER_1M_JSON: JSON mapping model -> { "input": <usd_per_1m>, "output": <usd_per_1m> }
    - MODEL_PRICING_JSON: JSON mapping model -> { "input_per_1k": <usd>, "output_per_1k": <usd> }
    """
    raw_1m = os.getenv("MODEL_PRICING_PER_1M_JSON")
    if raw_1m:
        try:
            data = json.loads(raw_1m)
            if isinstance(data, dict):
                return {
                    str(k): {"input": float(v.get("input")), "output": float(v.get("output"))}
                    for k, v in data.items()
                    if isinstance(v, dict) and "input" in v and "output" in v
                }
        except Exception:
            return {}

    raw = os.getenv("MODEL_PRICING_JSON")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                out: dict[str, dict[str, float]] = {}
                for k, v in data.items():
                    if not isinstance(v, dict):
                        continue
                    if "input_per_1k" in v and "output_per_1k" in v:
                        out[str(k)] = {
                            "input": float(v["input_per_1k"]) * 1000.0,
                            "output": float(v["output_per_1k"]) * 1000.0,
                        }
                return out
        except Exception:
            return {}

    return {}


def _resolve_pricing(model: str | None) -> Optional[dict[str, float]]:
    if not model:
        return None
    pricing = _load_model_pricing_per_1m()
    if not pricing:
        return None

    # Exact match first
    if model in pricing:
        return pricing[model]

    # Fuzzy: strip provider prefixes and match by prefix (e.g. "openai/gpt-4o" -> "gpt-4o")
    normalized = model.split("/")[-1]
    if normalized in pricing:
        return pricing[normalized]

    for k, v in pricing.items():
        if normalized.startswith(k) or k.startswith(normalized):
            return v
    return None


def calculate_llm_cost(prompt_tokens: int, completion_tokens: int, model: str | None) -> float:
    """
    Model-aware cost calculation (preferred).

    If pricing is not configured for the model, falls back to legacy fixed per-token estimation.
    """
    pricing = _resolve_pricing(model)
    if pricing:
        # pricing is USD per 1M tokens
        return (prompt_tokens / 1_000_000) * pricing["input"] + (completion_tokens / 1_000_000) * pricing["output"]

    # Fallback
    return prompt_tokens * INPUT_COST_PER_TOKEN + completion_tokens * OUTPUT_COST_PER_TOKEN


def estimate_llm_cost(input_content: str, output_content: str, model: str | None = None) -> float:
    """
    Estimate LLM cost from text content by estimating token usage, then applying model pricing.
    """
    token_usage = estimate_token_usage(input_content, output_content, model=model)
    return calculate_llm_cost(
        prompt_tokens=int(token_usage["prompt_tokens"]),
        completion_tokens=int(token_usage["completion_tokens"]),
        model=model,
    )


def estimate_token_usage(input_content: str, output_content: str, model: str | None = None) -> dict:
    """
    Estimate token usage for input and output content.
    
    Args:
        input_content: The input/prompt content
        output_content: The output/completion content
        
    Returns:
        dict with prompt_tokens, completion_tokens, and total_tokens
    """
    encoding = _get_encoding(model)
    prompt_tokens = len(encoding.encode(input_content))
    completion_tokens = len(encoding.encode(output_content))
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }


def estimate_embedding_cost(model, docs):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = sum(len(encoding.encode(str(doc))) for doc in docs)
    return total_tokens * EMBEDDING_COST

