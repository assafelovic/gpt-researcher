from __future__ import annotations

import logging
import os
import random
import re
import traceback
from typing import TYPE_CHECKING, Any

from colorama import Fore, Style

from gpt_researcher.llm_provider import GenericLLMProvider

if TYPE_CHECKING:
    from typing_extensions import Literal

    from gpt_researcher.config import Config
    from llm_fallbacks.config import LiteLLMBaseModelSpec


logger: logging.Logger = logging.getLogger(__name__)


MAX_FALLBACKS: int = 25


def _log_config_section(
    section_name: str,
    message: str,
    level: str = "INFO",
    verbose: bool = True,
) -> None:
    """Helper function for consistent config logging."""
    if not verbose:
        return
    colors: dict[str, str] = {
        "DEBUG": Fore.LIGHTBLACK_EX,
        "INFO": Fore.CYAN,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "SUCCESS": Fore.GREEN,
    }
    color: str = colors.get(level, Fore.WHITE)
    print(f"{color}[{level}] {section_name}: {message}{Style.RESET_ALL}")

def map_litellm_provider_to_gptr_provider(
    litellm_provider_name: str | None,
) -> str | None:
    """Maps LiteLLM provider names to GPT Researcher expected provider names.

    Key Requirements:
    - OpenRouter models: Keep provider as "openrouter"
    - All other models: Provider should be "litellm" (normalized for llm_fallbacks system)
    - This is ONLY for llm_fallbacks models, not user-configured models
    """
    if not litellm_provider_name or not litellm_provider_name.strip():
        return None

    name_lower: str = litellm_provider_name.lower()

    # OpenRouter models keep their original provider name
    if name_lower == "openrouter":
        return "openrouter"

    # All other providers from llm_fallbacks should be normalized to "litellm"
    # This ensures that non-OpenRouter models use the generic litellm provider
    # instead of their specific providers (google_genai, anthropic, etc.)
    return "litellm"


def generate_auto_fallbacks_from_free_models(
    free_models: list[tuple[str, LiteLLMBaseModelSpec]],
    model_type: Literal["embedding", "chat", "strategic_chat", "fast_chat"],
    clean_primary_model_id: str,
    fast_token_limit: int,
    smart_token_limit: int,
    strategic_token_limit: int,
    verbose_logging: bool = False,
) -> list[str]:
    """Extract auto-generation logic for reuse in manual fallback mode."""
    # Get required token limit based on model type
    required_token_limit: int = 0
    if model_type == "fast_chat":
        required_token_limit = fast_token_limit
    elif model_type == "strategic_chat":
        required_token_limit = strategic_token_limit
    elif model_type == "chat":
        required_token_limit = smart_token_limit

    # Filter models based on token limit and other criteria
    final_candidates: list[str] = []
    blacklisted_patterns: list[str] = GenericLLMProvider.MODEL_BLACKLIST
    filtered_counts: dict[str, int] = {
        "blacklisted": 0,
        "wrong_mode": 0,
        "insufficient_tokens": 0,
    }

    # Process free models
    for model_id, spec in free_models:
        # Skip blacklisted models
        blacklist_match: str | None = None
        for pattern in blacklisted_patterns:
            if re.search(pattern, model_id, re.IGNORECASE):
                blacklist_match = pattern
                break

        if blacklist_match and blacklist_match.strip():
            filtered_counts["blacklisted"] += 1
            continue

        # Skip non-matching model types
        model_mode: str = spec.get("mode", "unknown")
        if model_type == "embedding" and model_mode != "embedding":
            filtered_counts["wrong_mode"] += 1
            continue
        elif (
            model_type in {"chat", "strategic_chat", "fast_chat"}
            and model_mode != "chat"
        ):
            filtered_counts["wrong_mode"] += 1
            continue

        # Check token capacity for chat models
        if model_type in {"chat", "strategic_chat", "fast_chat"}:
            max_output_tokens: int = spec.get("max_output_tokens", 0)
            # Include models with 0 tokens (likely means unknown/not configured)
            # Only filter out models that have a known token limit that's insufficient
            if max_output_tokens > 0 and max_output_tokens < required_token_limit:
                filtered_counts["insufficient_tokens"] += 1
                continue

        # Model passed all filters
        final_candidates.append(model_id)

    # Summary debug logging
    logger.debug(
        f"Filtering summary for {model_type}: "
        f"blacklisted={filtered_counts['blacklisted']}, "
        f"wrong_mode={filtered_counts['wrong_mode']}, "
        f"insufficient_tokens={filtered_counts['insufficient_tokens']}, "
        f"accepted={len(final_candidates)}"
    )

    # Remove the primary model from fallbacks if present
    if clean_primary_model_id and clean_primary_model_id.strip():
        final_candidates: list[str] = [
            model_id
            for model_id in final_candidates
            if model_id != clean_primary_model_id
        ]

    # Convert model IDs to correct fallback format
    formatted_fallbacks: list[str] = []
    free_models_dict: dict[str, LiteLLMBaseModelSpec] = dict(free_models)

    # Separate OpenRouter models for prioritization (to match manual config pattern)
    openrouter_candidates: list[str] = []
    other_candidates: list[str] = []

    for model_id_key in final_candidates:
        spec: LiteLLMBaseModelSpec = free_models_dict.get(model_id_key, {})
        litellm_provider: str | None = spec.get("litellm_provider") or spec.get("provider")

        # Map litellm provider to GPT-Researcher supported provider
        mapped_provider: str | None = map_litellm_provider_to_gptr_provider(litellm_provider)

        # Check if this is an OpenRouter model (prioritize like manual config)
        # OpenRouter models can have various litellm_provider values but all map to "openrouter"
        if (
            mapped_provider == "openrouter"
            or litellm_provider == "openrouter"
            or model_id_key.startswith("openrouter/")
        ):
            openrouter_candidates.append(model_id_key)
        else:
            other_candidates.append(model_id_key)

    # Process OpenRouter models first (to match manual priority)
    prioritized_candidates: list[str] = openrouter_candidates + other_candidates

    for i, model_id_key in enumerate(prioritized_candidates):
        spec: LiteLLMBaseModelSpec = free_models_dict.get(model_id_key, {})
        litellm_provider: str | None = spec.get("litellm_provider") or spec.get("provider")

        # Map litellm provider to GPT-Researcher supported provider
        mapped_provider: str | None = map_litellm_provider_to_gptr_provider(litellm_provider)

        # Use mapped provider if available, fallback to original
        final_provider: str = mapped_provider or litellm_provider or "unknown"

        # Determine actual model name and format according to manual patterns
        if "/" in model_id_key:
            # e.g. "openrouter/meta-llama/llama-3-8b-instruct" -> "openrouter:meta-llama/llama-3-8b-instruct:free"
            split: list[str] = model_id_key.split("/", 1)
            provider_from_key, model_name_from_key = split[0], split[1]

            # If the key starts with a provider name, use the mapped version of that provider
            if provider_from_key in ["openrouter", "litellm"]:
                final_provider = provider_from_key
            # For models from llm_fallbacks, most should map to openrouter or litellm
            elif mapped_provider in ["openrouter", "litellm"]:
                final_provider = mapped_provider

        elif ":" in model_id_key:
            # Already in provider:model_name format - check if it needs :free suffix
            if model_id_key.endswith(":free"):
                # Already has :free suffix, don't add another
                formatted_fallbacks.append(model_id_key)
            else:
                # Add :free suffix to match manual format
                converted_model: str = f"{model_id_key}:free"
                formatted_fallbacks.append(converted_model)
            continue
        else:
            # Simple model name, use the mapped provider
            model_name_from_key: str = model_id_key

        # Check if model name already ends with :free to avoid double suffix
        if model_name_from_key.endswith(":free"):
            model_name_clean: str = model_name_from_key[:-5]  # Remove :free suffix
            suffix = ":free"
        else:
            model_name_clean = model_name_from_key
            suffix = ":free"

        # Format according to manual configuration patterns using mapped providers
        final_format: str = f"{final_provider}:{model_name_clean}{suffix}"
        formatted_fallbacks.append(final_format)

    # Final check for environment requirements
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not os.environ.get(
        "GOOGLE_CLOUD_PROJECT"
    ):
        formatted_fallbacks = [
            fb
            for fb in formatted_fallbacks
            if "google_vertexai" not in fb and "vertex_ai" not in fb
        ]

    # Apply MAX_FALLBACKS limit
    final_result: list[str] = formatted_fallbacks[:MAX_FALLBACKS]

    return final_result


def parse_model_fallbacks(
    fallbacks_str: str,
    model_type: Literal["embedding", "chat", "strategic_chat", "fast_chat"],
    primary_model_id: str,
    fast_token_limit: int = 3000,
    smart_token_limit: int = 6000,
    strategic_token_limit: int = 4000,
) -> list[str]:
    """Parse model fallbacks string into a list of model names."""
    if not fallbacks_str:
        return []

    # Clean the primary model ID to handle empty or "auto" values
    clean_primary_model_id: str = (
        ""
        if not primary_model_id or primary_model_id.strip().lower() == "auto"
        else primary_model_id
    )

    # For manual fallbacks - ALWAYS append FREE_MODELS to user-specified fallbacks
    if fallbacks_str.strip().lower() != "auto":
        raw_fallbacks: list[str] = [
            fb.strip() for fb in fallbacks_str.split(",") if fb.strip()
        ]
        parsed_fallbacks: list[str] = [
            fb
            for fb in raw_fallbacks
            if not clean_primary_model_id or fb != clean_primary_model_id
        ]

        # Deduplicate manual fallbacks
        seen: set[str] = set()
        manual_fallbacks: list[str] = [
            x for x in parsed_fallbacks if not (x in seen or seen.add(x))
        ]

        # Load FREE_MODELS for auto-generation
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS

            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
        else:
            from llm_fallbacks.config import FREE_MODELS

            free_models = FREE_MODELS

        # Generate auto fallbacks using the same logic as auto mode
        auto_fallbacks: list[str] = generate_auto_fallbacks_from_free_models(
            free_models,
            model_type,
            clean_primary_model_id,
            fast_token_limit,
            smart_token_limit,
            strategic_token_limit,
            verbose_logging=False,
        )

        # Combine manual + auto fallbacks, removing duplicates while preserving order
        combined_fallbacks: list[str] = manual_fallbacks.copy()
        seen_combined: set[str] = set(manual_fallbacks)

        for auto_fb in auto_fallbacks:
            if auto_fb not in seen_combined:
                combined_fallbacks.append(auto_fb)
                seen_combined.add(auto_fb)

        return combined_fallbacks[:MAX_FALLBACKS]

    # Auto-generate fallbacks
    try:
        # Load model specs from llm_fallbacks package
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS

            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
        else:
            from llm_fallbacks.config import FREE_MODELS

            free_models = FREE_MODELS

        # Use the enhanced method
        final_fallbacks_list: list[str] = generate_auto_fallbacks_from_free_models(
            free_models,
            model_type,
            clean_primary_model_id,
            fast_token_limit,
            smart_token_limit,
            strategic_token_limit,
            verbose_logging=False,
        )

        return final_fallbacks_list

    except Exception as e:
        if os.getenv("VERBOSE", "").lower() in ("true", "1"):
            traceback.print_exc()
        return []


def initialize_fallback_providers_for_type(
    fallback_str_list: list[str] | None = None,
    llm_type_name: Literal["smart", "fast", "strategic", "embedding"] | None = None,
    llm_kwargs: dict[str, Any] | None = None,
    chat_log: str | None = None,
    verbose: bool = True,
) -> list[GenericLLMProvider]:
    """Initialize fallback providers for a specific LLM type."""
    initialized_providers: list[GenericLLMProvider] = []
    if not fallback_str_list:
        return initialized_providers

    if llm_kwargs is None:
        llm_kwargs = {}

    for i, fallback_spec_str in enumerate(fallback_str_list):
        try:
            # Split into provider and model name
            if ":" not in fallback_spec_str:
                continue

            provider_name, model_name = fallback_spec_str.split(":", 1)

            # Fix OpenRouter model names to ensure they have the proper provider prefix
            if provider_name == "openrouter":
                # Check if model name needs a provider prefix
                if "/" not in model_name:
                    # This is likely a model that needs a provider prefix
                    # Common OpenRouter model patterns that need prefixes
                    if any(pattern in model_name.lower() for pattern in [
                        "gemini", "claude", "gpt", "llama", "mistral", "qwen", "deepseek"
                    ]):
                        # Try to determine the correct prefix based on model name
                        if "gemini" in model_name.lower():
                            model_name = f"google/{model_name}"
                        elif "claude" in model_name.lower():
                            model_name = f"anthropic/{model_name}"
                        elif "gpt" in model_name.lower():
                            model_name = f"openai/{model_name}"
                        elif "llama" in model_name.lower():
                            model_name = f"meta-llama/{model_name}"
                        elif "mistral" in model_name.lower():
                            model_name = f"mistralai/{model_name}"
                        elif "qwen" in model_name.lower():
                            model_name = f"qwen/{model_name}"
                        elif "deepseek" in model_name.lower():
                            model_name = f"deepseek/{model_name}"

            # Construct kwargs for the provider
            # Start with general llm_kwargs and add the specific model
            provider_kwargs: dict[str, Any] = llm_kwargs.copy()
            provider_kwargs["model"] = model_name
            provider_kwargs["verbose"] = verbose

            fallback_instance: GenericLLMProvider = GenericLLMProvider.from_provider(
                provider_name,
                chat_log=chat_log,
                **provider_kwargs,
            )
            initialized_providers.append(fallback_instance)

        except Exception as e:
            # Always show the traceback info if DEBUG_FALLBACKS is set
            if os.getenv("DEBUG_FALLBACKS", "").lower() in ("true", "1") or os.getenv(
                "VERBOSE", ""
            ).lower() in ("true", "1"):
                tb_str: str = traceback.format_exc()
                print(f"Traceback for '{fallback_spec_str}':\n{tb_str}")

    return initialized_providers


def set_llm_attributes(config_instance: Config) -> None:
    """Set LLM attributes for a config instance.

    Args:
        config_instance: The Config instance to set attributes on
    """
    # Parse fallbacks for each LLM type first (list of strings)
    fast_llm_fallback_str_list: list[str] = parse_model_fallbacks(
        config_instance.fast_llm_fallbacks,
        "fast_chat",
        config_instance.fast_llm or "",
        config_instance.fast_token_limit,
        config_instance.smart_token_limit,
        config_instance.strategic_token_limit,
    )
    smart_llm_fallback_str_list: list[str] = parse_model_fallbacks(
        config_instance.smart_llm_fallbacks,
        "chat",
        config_instance.smart_llm or "",
        config_instance.fast_token_limit,
        config_instance.smart_token_limit,
        config_instance.strategic_token_limit,
    )
    strategic_llm_fallback_str_list: list[str] = parse_model_fallbacks(
        config_instance.strategic_llm_fallbacks,
        "strategic_chat",
        config_instance.strategic_llm or "",
        config_instance.fast_token_limit,
        config_instance.smart_token_limit,
        config_instance.strategic_token_limit,
    )

    # If main LLM is empty or "auto", use the first fallback
    if not config_instance.fast_llm or config_instance.fast_llm.strip().lower() == "auto":
        if fast_llm_fallback_str_list:
            config_instance.fast_llm = fast_llm_fallback_str_list[0]

    if not config_instance.smart_llm or config_instance.smart_llm.strip().lower() == "auto":
        if smart_llm_fallback_str_list:
            config_instance.smart_llm = smart_llm_fallback_str_list[0]

    if not config_instance.strategic_llm or config_instance.strategic_llm.strip().lower() == "auto":
        if strategic_llm_fallback_str_list:
            config_instance.strategic_llm = strategic_llm_fallback_str_list[0]

    # Now parse the main LLMs (which might have been updated from fallbacks)
    # Import the Config class to access the static parse_llm method
    from gpt_researcher.config.config import Config
    config_instance.fast_llm_provider, config_instance.fast_llm_model = Config.parse_llm(config_instance.fast_llm)
    config_instance.smart_llm_provider, config_instance.smart_llm_model = Config.parse_llm(config_instance.smart_llm)
    config_instance.strategic_llm_provider, config_instance.strategic_llm_model = Config.parse_llm(config_instance.strategic_llm)

    # Remove the main model from fallbacks to avoid duplication
    if config_instance.fast_llm and config_instance.fast_llm in fast_llm_fallback_str_list:
        fast_llm_fallback_str_list.remove(config_instance.fast_llm)
    if config_instance.smart_llm and config_instance.smart_llm in smart_llm_fallback_str_list:
        smart_llm_fallback_str_list.remove(config_instance.smart_llm)
    if config_instance.strategic_llm and config_instance.strategic_llm in strategic_llm_fallback_str_list:
        strategic_llm_fallback_str_list.remove(config_instance.strategic_llm)

    # Initialize fallback providers (use cached values if available)
    # Import the Config class to access class variables
    if not Config._fallbacks_initialized:
        Config._cached_fast_llm_fallback_providers = initialize_fallback_providers_for_type(fast_llm_fallback_str_list, "fast", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._cached_smart_llm_fallback_providers = initialize_fallback_providers_for_type(smart_llm_fallback_str_list, "smart", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._cached_strategic_llm_fallback_providers = initialize_fallback_providers_for_type(strategic_llm_fallback_str_list, "strategic", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._fallbacks_initialized = True

    # Assign the cached providers to this instance
    config_instance.fast_llm_fallback_providers = Config._cached_fast_llm_fallback_providers
    config_instance.smart_llm_fallback_providers = Config._cached_smart_llm_fallback_providers
    config_instance.strategic_llm_fallback_providers = Config._cached_strategic_llm_fallback_providers
