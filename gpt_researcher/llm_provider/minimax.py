"""MiniMax endpoints and model metadata."""

from __future__ import annotations

import os
from typing import Literal


MINIMAX_ENDPOINTS = {
    "global_en": {
        "openai": "https://api.minimax.io/v1",
        "anthropic": "https://api.minimax.io/anthropic",
    },
    "cn_zh": {
        "openai": "https://api.minimaxi.com/v1",
        "anthropic": "https://api.minimaxi.com/anthropic",
    },
}

MINIMAX_MODEL_SPECS = {
    "MiniMax-M3": {
        "context_window": 1_000_000,
        "input_modalities": ("text", "image", "video"),
        "thinking": ("adaptive", "disabled"),
        "pricing_usd_per_million_tokens": {
            "input": 0.3,
            "output": 1.2,
            "cache_read": 0.06,
            "cache_write": None,
        },
        "pricing_tiers_usd_per_million_tokens": (
            {
                "service_tier": "standard",
                "input_tokens_lte": 512_000,
                "input": 0.3,
                "output": 1.2,
                "cache_read": 0.06,
                "cache_write": None,
            },
            {
                "service_tier": "standard",
                "input_tokens_gt": 512_000,
                "input": 0.6,
                "output": 2.4,
                "cache_read": 0.12,
                "cache_write": None,
            },
            {
                "service_tier": "priority",
                "input_tokens_lte": 512_000,
                "input": 0.45,
                "output": 1.8,
                "cache_read": 0.09,
                "cache_write": None,
            },
            {
                "service_tier": "priority",
                "input_tokens_gt": 512_000,
                "input": 0.9,
                "output": 3.6,
                "cache_read": 0.18,
                "cache_write": None,
            },
        ),
    },
    "MiniMax-M2.7": {
        "context_window": 204_800,
        "input_modalities": ("text",),
        "thinking": ("always_on",),
        "pricing_usd_per_million_tokens": {
            "input": 0.3,
            "output": 1.2,
            "cache_read": 0.06,
            "cache_write": 0.375,
        },
    },
}


def get_minimax_base_url(protocol: Literal["openai", "anthropic"]) -> str:
    """Resolve a regional MiniMax endpoint for the requested protocol."""
    env_name = (
        "MINIMAX_BASE_URL"
        if protocol == "openai"
        else "MINIMAX_ANTHROPIC_BASE_URL"
    )
    region = os.getenv("MINIMAX_REGION", "global_en")
    base_url = os.getenv(env_name) or MINIMAX_ENDPOINTS.get(region, {}).get(protocol)
    if not base_url:
        supported_regions = ", ".join(sorted(MINIMAX_ENDPOINTS))
        raise ValueError(
            f"Unsupported MINIMAX_REGION={region!r}; choose one of {supported_regions}"
        )

    base_url = base_url.rstrip("/")
    required_suffix = "/v1" if protocol == "openai" else "/anthropic"
    if not base_url.endswith(required_suffix):
        raise ValueError(
            f"{env_name} must end with {required_suffix}; received {base_url!r}"
        )
    return base_url
