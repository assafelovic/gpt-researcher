"""Cost estimation utilities for LLM API usage."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import tiktoken

# Per OpenAI Pricing Page: https://openai.com/api/pricing/
ENCODING_MODEL = "o200k_base"
INPUT_COST_PER_TOKEN = 0.000005
OUTPUT_COST_PER_TOKEN = 0.000015
IMAGE_INFERENCE_COST = 0.003825
EMBEDDING_COST = 0.02 / 1000000  # Assumes new ada-3-small

logger = logging.getLogger(__name__)

ANTHROPIC_MODEL_PRICING = (
    (("claude-opus-4-7",), 5.0, 25.0),
    (("claude-opus-4-6",), 5.0, 25.0),
    (("claude-opus-4-5", "claude-4-opus"), 5.0, 25.0),
    (("claude-opus-4-1",), 15.0, 75.0),
    (("claude-opus-4",), 15.0, 75.0),
    (("claude-sonnet-4-6",), 3.0, 15.0),
    (("claude-sonnet-4-5", "claude-4-sonnet"), 3.0, 15.0),
    (("claude-sonnet-4",), 3.0, 15.0),
    (("claude-haiku-4-5",), 1.0, 5.0),
    (("claude-3-5-haiku",), 0.8, 4.0),
)

ANTHROPIC_US_INFERENCE_GEO_MODELS = (
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
)


def estimate_llm_cost(input_content: str, output_content: str) -> float:
    """Estimate the cost of an LLM API call based on input and output content.

    Cost estimation is based on OpenAI pricing and may vary for other models.

    Args:
        input_content: The input text sent to the LLM.
        output_content: The output text received from the LLM.

    Returns:
        The estimated cost in USD.
    """
    encoding = tiktoken.get_encoding(ENCODING_MODEL)
    input_tokens = encoding.encode(input_content)
    output_tokens = encoding.encode(output_content)
    input_costs = len(input_tokens) * INPUT_COST_PER_TOKEN
    output_costs = len(output_tokens) * OUTPUT_COST_PER_TOKEN
    return input_costs + output_costs


def _mapping_to_dict(value: Mapping[str, Any] | Any | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return dict(value.model_dump())
    return {}


def _resolve_anthropic_model_name(
    model: str | None,
    response_metadata: Mapping[str, Any] | None = None,
) -> str:
    metadata = _mapping_to_dict(response_metadata)
    return str(
        metadata.get("model")
        or metadata.get("model_name")
        or model
        or ""
    ).lower()


def _extract_anthropic_usage(
    response_metadata: Mapping[str, Any] | None = None,
    usage_metadata: Mapping[str, Any] | Any | None = None,
) -> dict[str, int] | None:
    metadata = _mapping_to_dict(response_metadata)
    usage = _mapping_to_dict(metadata.get("usage"))

    if usage:
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if input_tokens is not None and output_tokens is not None:
            return {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
            }

    usage = _mapping_to_dict(usage_metadata)
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if input_tokens is None or output_tokens is None:
        return None

    return {
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
    }


def _get_anthropic_pricing(model_name: str) -> tuple[float, float] | None:
    normalized_model_name = model_name.lower()
    for patterns, input_price_per_mtok, output_price_per_mtok in ANTHROPIC_MODEL_PRICING:
        if any(pattern in normalized_model_name for pattern in patterns):
            return input_price_per_mtok, output_price_per_mtok
    return None


def _get_anthropic_pricing_multiplier(
    model_name: str,
    request_options: Mapping[str, Any] | None = None,
) -> float:
    if not request_options:
        return 1.0

    inference_geo = str(request_options.get("inference_geo", "")).lower()
    if inference_geo != "us":
        return 1.0

    if any(pattern in model_name for pattern in ANTHROPIC_US_INFERENCE_GEO_MODELS):
        return 1.1

    return 1.0


def calculate_anthropic_cost(
    model: str | None,
    response_metadata: Mapping[str, Any] | None = None,
    usage_metadata: Mapping[str, Any] | Any | None = None,
    request_options: Mapping[str, Any] | None = None,
) -> float | None:
    usage = _extract_anthropic_usage(response_metadata=response_metadata, usage_metadata=usage_metadata)
    if not usage:
        return None

    model_name = _resolve_anthropic_model_name(model=model, response_metadata=response_metadata)
    pricing = _get_anthropic_pricing(model_name)
    if pricing is None:
        logger.warning(
            "Missing Anthropic pricing rule for model '%s'; falling back to token estimator.",
            model_name or model,
        )
        return None

    input_price_per_mtok, output_price_per_mtok = pricing
    multiplier = _get_anthropic_pricing_multiplier(model_name, request_options=request_options)
    input_cost = usage["input_tokens"] * input_price_per_mtok / 1_000_000
    output_cost = usage["output_tokens"] * output_price_per_mtok / 1_000_000
    return (input_cost + output_cost) * multiplier


def calculate_llm_cost(
    llm_provider: str | None,
    model: str | None,
    input_content: str,
    output_content: str,
    response_metadata: Mapping[str, Any] | None = None,
    usage_metadata: Mapping[str, Any] | Any | None = None,
    request_options: Mapping[str, Any] | None = None,
) -> float:
    if llm_provider == "anthropic":
        anthropic_cost = calculate_anthropic_cost(
            model=model,
            response_metadata=response_metadata,
            usage_metadata=usage_metadata,
            request_options=request_options,
        )
        if anthropic_cost is not None:
            return anthropic_cost

    return estimate_llm_cost(input_content, output_content)


def estimate_embedding_cost(model: str, docs: list) -> float:
    """Estimate the cost of embedding documents.

    Args:
        model: The embedding model name.
        docs: List of documents to embed.

    Returns:
        The estimated embedding cost in USD.
    """
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = sum(len(encoding.encode(str(doc))) for doc in docs)
    return total_tokens * EMBEDDING_COST

