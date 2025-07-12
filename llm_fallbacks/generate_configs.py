#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import uuid

from pathlib import Path

if not importlib.util.find_spec("llm_fallbacks"):
    import sys

    sys.path.append(str(Path(__file__).parents[1]))
from typing import TYPE_CHECKING, Any

from llm_fallbacks.config import ALL_MODELS, CUSTOM_PROVIDERS, FREE_MODELS
from llm_fallbacks.core import calculate_cost_per_token

if TYPE_CHECKING:
    import logging

    from llm_fallbacks.config import CustomProviderConfig, LiteLLMYAMLConfig


logger: logging.Logger = logging.getLogger(__name__)


def to_litellm_config_yaml(
    providers: list[CustomProviderConfig],
    free_only: bool = False,
    online_only: bool = False,
) -> LiteLLMYAMLConfig:
    """Convert the provider config to a LiteLLM YAML config format."""
    # Create base config with all possible settings
    config: LiteLLMYAMLConfig = {
        "cache": {
            "host": "localhost",
            "mode": "default_off",
            "namespace": "litellm.caching.caching",
            "port": 6379,
            "supported_call_types": [
                "acompletion",
                "atext_completion",
                "aembedding",
                "atranscription",
            ],
            "ttl": 600,
            "type": "redis",
        },
        "general_settings": {
            "master_key": f"sk-{uuid.uuid4().hex}",
#            "alerting": ["slack", "email"],
            "proxy_batch_write_at": 60,  # Batch write spend updates every 60s
            "database_connection_pool_limit": 10,  # limit the number of database connections to = MAX Number of DB Connections/Number of instances of litellm proxy (Around 10-20 is good number)
            "alerting_threshold": 0,
            "allow_requests_on_db_unavailable": True,
            "allowed_routes": [],
            "background_health_checks": True,
            "database_url": f"postgresql://postgres:{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@localhost:5432/postgres",
            "disable_adding_master_key_hash_to_db": False,
            "disable_master_key_return": False,
            "disable_reset_budget": False,
            "disable_retry_on_max_parallel_request_limit_error": False,
            "disable_spend_logs": False,
            "enable_jwt_auth": False,
            "enforce_user_param": False,
            "global_max_parallel_requests": 0,
            "health_check_interval": 300,
            "infer_model_from_keys": True,
            "max_parallel_requests": 0,
            "use_client_credentials_pass_through_routes": False,
        },
        "litellm_settings": {
            "callbacks": ["otel"],
            "content_policy_fallbacks": [],
            "context_window_fallbacks": [],
            "default_fallbacks": [],
            "failure_callback": ["sentry"],
            "force_ipv4": True,
            "json_logs": True,
            "redact_user_api_key_info": True,
            "request_timeout": 600,
            "service_callbacks": ["datadog", "prometheus"],
            "set_verbose": False,
            "turn_off_message_logging": False,
        },
        "model_list": [],
        "router_settings": {
            "allowed_fails": 3,
            "allowed_fails_policy": {
                "BadRequestErrorAllowedFails": 1000,
                "AuthenticationErrorAllowedFails": 10,
                "TimeoutErrorAllowedFails": 12,
                "RateLimitErrorAllowedFails": 10000,
                "ContentPolicyViolationErrorAllowedFails": 15,
                "InternalServerErrorAllowedFails": 20,
            },
            "cooldown_time": 30,
            "disable_cooldowns": False,
            "enable_pre_call_checks": True,
            "enable_tag_filtering": True,
            "fallbacks": [],
            "retry_policy": {
                "AuthenticationErrorRetries": 3,
                "TimeoutErrorRetries": 3,
                "RateLimitErrorRetries": 3,
                "ContentPolicyViolationErrorRetries": 4,
                "InternalServerErrorRetries": 4,
            },
            "routing_strategy": "simple-shuffle",
        },
    }

    for p in providers:
        for model_name, model_spec in (p.free_models if free_only else p.model_specs).items():
            is_free: bool = calculate_cost_per_token(model_spec) == 0.0
            is_local: bool = (
                model_name.strip().casefold().startswith("ollama/")
                or model_name.strip().casefold().startswith("vllm/")
                or model_name.strip().casefold().startswith("xinference/")
                or model_name.strip().casefold().startswith("lmstudio/")
                or "127.0.0.1" in p.base_url
                or "localhost" in p.base_url.strip().casefold()
                or "0.0.0.0" in p.base_url
            )
            if free_only and (not is_free or is_local):
                continue

            key_name: str = model_name if "/" in model_name else f"{p.provider_name}/{model_name}"
            model_entry: dict[str, Any] = {
                "model_name": key_name,
                "litellm_params": {
                    "model": (key_name if key_name.strip().casefold().startswith("openai/") else f"openai/{key_name}"),
                    "api_base": p.base_url,
                    **{"api_key": f"os.environ/{p.api_env_key_name}"},
                    **({} if p.api_version is None else {"api_version": p.api_version}),
                    **{k: v for k, v in model_spec.items()},
                },
            }
            config["model_list"].append(model_entry)  # pyright: ignore[reportArgumentType]

            # Determine suitable fallbacks based on mode and cost
            suitable_fallbacks: list[str] = []
            total_fallbacks_found: int = 0
            total_fallbacks_required: int = 25
            for k, v in FREE_MODELS:
                k_name: str = (
                    k
                    if k.strip().casefold().startswith(f"{v.get('litellm_provider')}/".strip().casefold()) and k not in suitable_fallbacks
                    else f"{v.get('litellm_provider')}/{k}"
                )
                if k.strip().casefold() == model_name.strip().casefold():  # Avoid self-referential fallbacks
                    continue
                if (
                    v.get("mode") is not None
                    and model_spec.get("mode") is not None
                    and v.get("mode") != str(model_spec.get("mode")).casefold().strip()
                ):
                    continue
                if (
                    v.get("supports_vision") is not None
                    and model_spec.get("supports_vision") is not None
                    and v.get("supports_vision") != str(model_spec.get("supports_vision")).casefold().strip()
                ):
                    continue
                if (
                    v.get("supports_embedding_image_input") is not None
                    and model_spec.get("supports_embedding_image_input") is not None
                    and v.get("supports_embedding_image_input") != str(model_spec.get("supports_embedding_image_input")).casefold().strip()
                ):
                    continue
                if (
                    v.get("supports_audio_input") is not None
                    and model_spec.get("supports_audio_input") is not None
                    and v.get("supports_audio_input") != str(model_spec.get("supports_audio_input")).casefold().strip()
                ):
                    continue
                if (
                    v.get("supports_audio_output") is not None
                    and model_spec.get("supports_audio_output") is not None
                    and v.get("supports_audio_output") != str(model_spec.get("supports_audio_output")).casefold().strip()
                ):
                    continue
                if (
                    model_spec.get("mode") is not None
                    and str(model_spec.get("mode")).casefold().strip() != "chat"
                ):
                    total_fallbacks_required = 125
                if online_only and (
                    k.strip().casefold().startswith("ollama/")
                    or k.strip().casefold().startswith("vllm/")
                    or k.strip().casefold().startswith("xinference/")
                    or k.strip().casefold().startswith("lmstudio/")
                    or "127.0.0.1" in p.base_url
                    or "localhost" in p.base_url.strip().casefold()
                    or "0.0.0.0" in p.base_url
                ):
                    continue
                suitable_fallbacks.append(k_name)
                total_fallbacks_found += 1
                if total_fallbacks_found >= total_fallbacks_required:
                    break

            if suitable_fallbacks:
                fallback_list: list[dict[str, list[str]]] = config["router_settings"].setdefault("fallbacks", [])
                fallback_entry: dict[str, list[str]] = {model_name: suitable_fallbacks}
                fallback_list.append(fallback_entry)

    return config


if __name__ == "__main__":
    logger.info("Saving custom_providers.json")
    Path("custom_providers.json").absolute().write_text(
        json.dumps(
            [provider.to_dict() for provider in CUSTOM_PROVIDERS],
            indent=4,
            ensure_ascii=True,
        ),
    )
    logger.info("Saving all_models.json")
    Path("all_models.json").absolute().write_text(
        json.dumps(
            {model: spec for model, spec in ALL_MODELS},
            indent=4,
            ensure_ascii=True,
        ),
    )
    logger.info("Saving free_chat_models.json")
    Path("free_chat_models.json").absolute().write_text(
        json.dumps(
            {model: spec for model, spec in FREE_MODELS},
            indent=4,
            ensure_ascii=True,
        ),
    )

    # Generate and save LiteLLM config files
    try:
        import yaml

        logger.info("Saving litellm_config_free.yaml")
        Path("litellm_config_free.yaml").write_text(
            yaml.dump(
                to_litellm_config_yaml(CUSTOM_PROVIDERS, free_only=True),
                sort_keys=False,
                allow_unicode=True,
            ),
            errors="replace",
            encoding="utf-8",
        )
        logger.info("Saving litellm_config.yaml")
        Path("litellm_config.yaml").write_text(
            yaml.dump(
                to_litellm_config_yaml(CUSTOM_PROVIDERS, free_only=False),
                sort_keys=False,
                allow_unicode=True,
            ),
            errors="replace",
            encoding="utf-8",
        )
    except ImportError as e:
        logger.warning(f"Failed to generate YAML configs: {e.__class__.__name__}: {e}")
