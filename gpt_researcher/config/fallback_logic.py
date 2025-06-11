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


def _log_fallback_summary(
    model_type: str,
    primary_model: str,
    fallbacks: list[str],
    max_display: int = 5,
    verbose: bool = True,
) -> None:
    """Log a concise summary of fallback configuration."""
    if not fallbacks:
        _log_config_section(
            "FALLBACKS",
            f"No fallbacks configured for {model_type.upper()}",
            "WARN",
            verbose,
        )
        return

    display_count: int = min(len(fallbacks), max_display)
    fallback_preview: list[str] = fallbacks[:display_count]
    more_indicator: str = (
        f" (+{len(fallbacks) - display_count} more)"
        if len(fallbacks) > max_display
        else ""
    )

    _log_config_section(
        "FALLBACKS",
        f"{model_type.upper()}: {primary_model or 'auto'} → {display_count} fallbacks{more_indicator}",
        "INFO",
        verbose,
    )

    # Log first few fallbacks with provider grouping
    provider_groups: dict[str, list[str]] = {}
    for fb in fallback_preview:
        provider: str = fb.split(":")[0] if ":" in fb else "unknown"
        provider_groups.setdefault(provider, []).append(fb.split(":", 1)[1] if ":" in fb else fb)

    for provider, models in provider_groups.items():
        model_list: str = ", ".join(models[:3])
        if len(models) > 3:
            model_list += f" (+{len(models) - 3})"
        _log_config_section("FALLBACKS", f"  └─ {provider}: {model_list}", "INFO", verbose)


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

    # Debug logging for production use
    logger.debug(f"Processing {len(free_models)} FREE_MODELS for {model_type}")
    logger.debug(f"Required token limit: {required_token_limit}")
    logger.debug(f"Primary model to exclude: '{clean_primary_model_id}'")

    if verbose_logging:
        _log_config_section(
            "FREE_MODELS",
            f"Processing {len(free_models)} FREE_MODELS for {model_type}",
            "DEBUG",
        )
        _log_config_section(
            "FREE_MODELS",
            f"Required token limit: {required_token_limit}",
            "DEBUG",
        )
        _log_config_section(
            "FREE_MODELS",
            f"Primary model to exclude: '{clean_primary_model_id}'",
            "DEBUG",
        )

    # Filter models based on token limit and other criteria
    final_candidates: list[str] = []
    blacklisted_patterns: list[str] = GenericLLMProvider.MODEL_BLACKLIST
    filtered_counts: dict[str, int] = {
        "blacklisted": 0,
        "wrong_mode": 0,
        "insufficient_tokens": 0,
    }

    # Track examples for detailed logging
    accepted_examples: list[tuple[str, dict]] = []
    blacklisted_examples: list[str] = []
    wrong_mode_examples: list[tuple[str, str]] = []
    insufficient_token_examples: list[tuple[str, int]] = []

    # Debug logging for blacklist patterns
    logger.debug(f"Blacklist patterns: {blacklisted_patterns}")

    if verbose_logging:
        _log_config_section(
            "FREE_MODELS",
            f"Blacklist patterns: {blacklisted_patterns}",
            "DEBUG",
        )

    # Process free models with detailed debug logging
    for model_id, spec in free_models:
        # Skip blacklisted models
        blacklist_match: str | None = None
        for pattern in blacklisted_patterns:
            if re.search(pattern, model_id, re.IGNORECASE):
                blacklist_match = pattern
                break

        if blacklist_match and blacklist_match.strip():
            filtered_counts["blacklisted"] += 1
            logger.debug(
                f"Model '{model_id}' FILTERED OUT: blacklisted (matches pattern '{blacklist_match}')"
            )
            if verbose_logging and len(blacklisted_examples) < 5:
                blacklisted_examples.append(model_id)
            continue

        # Skip non-matching model types
        model_mode: str = spec.get("mode", "unknown")
        if model_type == "embedding" and model_mode != "embedding":
            filtered_counts["wrong_mode"] += 1
            logger.debug(f"Model '{model_id}' FILTERED OUT: wrong mode (expected 'embedding', got '{model_mode}')")
            if verbose_logging and len(wrong_mode_examples) < 5:
                wrong_mode_examples.append((model_id, model_mode))
            continue
        elif (
            model_type in {"chat", "strategic_chat", "fast_chat"}
            and model_mode != "chat"
        ):
            filtered_counts["wrong_mode"] += 1
            logger.debug(f"Model '{model_id}' FILTERED OUT: wrong mode (expected 'chat', got '{model_mode}')")
            if verbose_logging and len(wrong_mode_examples) < 5:
                wrong_mode_examples.append((model_id, model_mode))
            continue

        # Check token capacity for chat models
        if model_type in {"chat", "strategic_chat", "fast_chat"}:
            max_output_tokens: int = spec.get("max_output_tokens", 0)
            # Include models with 0 tokens (likely means unknown/not configured)
            # Only filter out models that have a known token limit that's insufficient
            if max_output_tokens > 0 and max_output_tokens < required_token_limit:
                filtered_counts["insufficient_tokens"] += 1
                logger.debug(f"Model '{model_id}' FILTERED OUT: insufficient tokens ({max_output_tokens} < {required_token_limit})")
                if verbose_logging and len(insufficient_token_examples) < 5:
                    insufficient_token_examples.append((model_id, max_output_tokens))
                continue

        # Model passed all filters
        final_candidates.append(model_id)
        provider: str = spec.get("litellm_provider", "unknown")
        tokens: int = spec.get("max_output_tokens", 0)
        logger.debug(f"Model '{model_id}' ACCEPTED: provider={provider}, tokens={tokens}, mode={model_mode}")
        if verbose_logging and len(accepted_examples) < 10:
            accepted_examples.append((model_id, dict(spec)))

    # Summary debug logging
    logger.debug(
        f"Filtering summary for {model_type}: "
        f"blacklisted={filtered_counts['blacklisted']}, "
        f"wrong_mode={filtered_counts['wrong_mode']}, "
        f"insufficient_tokens={filtered_counts['insufficient_tokens']}, "
        f"accepted={len(final_candidates)}"
    )

    if verbose_logging:
        # Log filtering examples
        if blacklisted_examples:
            # Randomly sample 3 blacklisted examples instead of always showing the first 3
            sample_count: int = min(3, len(blacklisted_examples))
            random_blacklisted: list[str] = random.sample(
                blacklisted_examples,
                sample_count,
            )
            _log_config_section(
                "FREE_MODELS",
                f"Blacklisted examples: {random_blacklisted}{'...' if len(blacklisted_examples) > 3 else ''}",
                "INFO",
            )
        if wrong_mode_examples:
            # Randomly sample 3 wrong mode examples instead of always showing the first 3
            sample_count: int = min(3, len(wrong_mode_examples))
            random_wrong_mode: list[tuple[str, str]] = random.sample(wrong_mode_examples, sample_count)
            mode_examples: list[str] = [f"{model} (mode: {mode})" for model, mode in random_wrong_mode]
            _log_config_section(
                "FREE_MODELS",
                f"Wrong mode examples: {mode_examples}{'...' if len(wrong_mode_examples) > 3 else ''}",
                "DEBUG",
            )
        if insufficient_token_examples:
            # Randomly sample 3 insufficient token examples instead of always showing the first 3
            sample_count = min(3, len(insufficient_token_examples))
            random_insufficient_tokens: list[tuple[str, int]] = random.sample(
                insufficient_token_examples, sample_count
            )
            token_examples: list[str] = [
                f"{model} ({tokens} tokens)"
                for model, tokens in random_insufficient_tokens
            ]
            _log_config_section(
                "FREE_MODELS",
                f"Insufficient tokens examples: {token_examples}{'...' if len(insufficient_token_examples) > 3 else ''}",
                "WARN",
            )

        # Log accepted examples
        if accepted_examples:
            _log_config_section(
                "FREE_MODELS",
                f"Accepted {len(final_candidates)} models. Examples:",
                "INFO",
            )
            # Randomly sample 5 accepted examples instead of always showing the first 5
            sample_count: int = min(5, len(accepted_examples))
            random_accepted: list[tuple[str, dict[str, Any]]] = random.sample(
                accepted_examples,
                sample_count,
            )
            for model_id, spec in random_accepted:
                provider = spec.get("litellm_provider", "unknown")
                tokens: int = spec.get("max_output_tokens", 0)
                mode: str = spec.get("mode", "unknown")
                _log_config_section(
                    "FREE_MODELS",
                    f"  ✅ {model_id} (provider: {provider}, tokens: {tokens}, mode: {mode})",
                    "DEBUG",
                )
            if len(accepted_examples) > 5:
                _log_config_section(
                    "FREE_MODELS",
                    f"  ... and {len(final_candidates) - 5} more",
                    "DEBUG",
                )

    # Remove the primary model from fallbacks if present
    if clean_primary_model_id and clean_primary_model_id.strip():
        before_count: int = len(final_candidates)
        final_candidates: list[str] = [
            model_id
            for model_id in final_candidates
            if model_id != clean_primary_model_id
        ]
        if before_count != len(final_candidates):
            logger.debug(f"Removed primary model '{clean_primary_model_id}' from candidates")
        if verbose_logging and before_count != len(final_candidates):
            _log_config_section(
                "FREE_MODELS",
                f"Removed primary model '{clean_primary_model_id}' from candidates",
                "DEBUG",
            )

    # Convert model IDs to correct fallback format
    formatted_fallbacks: list[str] = []
    free_models_dict: dict[str, LiteLLMBaseModelSpec] = dict(free_models)
    conversion_examples: list[tuple[str, str, dict[str, Any]]] = []

    logger.debug(f"Converting {len(final_candidates)} candidates to fallback format...")

    if verbose_logging:
        _log_config_section(
            "FREE_MODELS",
            f"Converting {len(final_candidates)} candidates to fallback format...",
            "DEBUG",
        )

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

    logger.debug(f"Prioritized {len(openrouter_candidates)} OpenRouter models first")

    if verbose_logging and openrouter_candidates:
        _log_config_section(
            "FREE_MODELS",
            f"Prioritized {len(openrouter_candidates)} OpenRouter models (matching manual config pattern)",
            "DEBUG",
        )

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
                logger.debug(f"Model '{model_id_key}' converted to '{model_id_key}' (already has :free suffix)")
            else:
                # Add :free suffix to match manual format
                converted_model: str = f"{model_id_key}:free"
                formatted_fallbacks.append(converted_model)
                logger.debug(f"Model '{model_id_key}' converted to '{converted_model}' (added :free suffix)")
            if verbose_logging and len(conversion_examples) < 5:
                conversion_examples.append((model_id_key, formatted_fallbacks[-1], dict(spec)))
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
        logger.debug(
            f"Model '{model_id_key}' converted to '{final_format}' (provider:  {litellm_provider} → {final_provider})"
        )

        if verbose_logging and len(conversion_examples) < 5:
            conversion_examples.append((model_id_key, final_format, dict(spec)))

    if verbose_logging and conversion_examples:
        _log_config_section(
            "FREE_MODELS",
            "Conversion examples (matching manual format):",
            "DEBUG",
        )
        for original, converted, spec in conversion_examples:
            litellm_prov: str = spec.get("litellm_provider", "unknown")
            mapped_prov: str | None = map_litellm_provider_to_gptr_provider(
                litellm_prov
            )
            _log_config_section(
                "FREE_MODELS",
                f"  {original} → {converted} (litellm: {litellm_prov}, mapped: {mapped_prov})",
                "DEBUG",
            )

    # Final check for environment requirements
    pre_env_count: int = len(formatted_fallbacks)
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not os.environ.get(
        "GOOGLE_CLOUD_PROJECT"
    ):
        vertex_models_filtered: list[str] = [
            fb
            for fb in formatted_fallbacks
            if "google_vertexai" in fb or "vertex_ai" in fb
        ]
        formatted_fallbacks = [
            fb
            for fb in formatted_fallbacks
            if "google_vertexai" not in fb and "vertex_ai" not in fb
        ]
        if pre_env_count != len(formatted_fallbacks):
            filtered_count: int = pre_env_count - len(formatted_fallbacks)
            logger.debug(
                f"Filtered {filtered_count} Google Vertex AI models (missing credentials): {vertex_models_filtered}"
            )
        if verbose_logging and pre_env_count != len(formatted_fallbacks):
            filtered_count: int = pre_env_count - len(formatted_fallbacks)
            _log_config_section(
                "FREE_MODELS",
                f"Filtered {filtered_count} Google Vertex AI models (missing credentials)",
                "DEBUG",
            )

    # Apply MAX_FALLBACKS limit
    if len(formatted_fallbacks) > MAX_FALLBACKS:
        logger.debug(
            f"Limiting fallbacks from {len(formatted_fallbacks)} to {MAX_FALLBACKS} models"
        )
        logger.debug(f"Models beyond limit: {formatted_fallbacks[MAX_FALLBACKS:]}")

    final_result: list[str] = formatted_fallbacks[:MAX_FALLBACKS]

    # Final debug summary
    logger.debug(
        f"Final fallback generation complete for {model_type}: {len(final_result)} models selected"
    )
    logger.debug(f"Final models: {final_result}")

    if verbose_logging:
        _log_config_section(
            "FREE_MODELS",
            f"Final result: {len(final_result)} FREE_MODELS selected (max {MAX_FALLBACKS})",
        )
        _log_config_section(
            "FREE_MODELS",
            f"Filter summary: {dict(filtered_counts)}",
            "DEBUG",
        )

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

        if manual_fallbacks:
            _log_config_section(
                "FALLBACK PARSE",
                f"Manual fallbacks for {model_type}: {len(manual_fallbacks)} user-specified models",
                "DEBUG",
            )
        elif fallbacks_str:
            _log_config_section(
                "FALLBACK PARSE",
                f"No valid manual fallbacks found for {model_type} after parsing",
                "WARN",
            )
            manual_fallbacks = []

        # Now auto-generate FREE_MODELS and append them to manual fallbacks
        _log_config_section(
            "FALLBACK PARSE",
            "Auto-generating FREE_MODELS to append to manual fallbacks...",
            "DEBUG",
        )

        # Load FREE_MODELS for auto-generation
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS

            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
            _log_config_section(
                "FALLBACK PARSE",
                f"Loaded {len(free_models)} free embedding models from llm_fallbacks",
                "DEBUG",
            )
        else:
            from llm_fallbacks.config import FREE_MODELS

            free_models = FREE_MODELS
            _log_config_section(
                "FALLBACK PARSE",
                f"Loaded {len(free_models)} free chat models from llm_fallbacks",
            )

        # Show sample of what we loaded
        if free_models:
            # Randomly sample 3 models instead of always showing the first 3
            sample_count: int = min(3, len(free_models))
            sample_models: list[tuple[str, LiteLLMBaseModelSpec]] = random.sample(
                free_models, sample_count
            )
            _log_config_section(
                "FALLBACK PARSE",
                f"Random sample of {sample_count} FREE_MODELS loaded:",
                "DEBUG",
            )
            for model_id, spec in sample_models:
                provider: str | None = spec.get("litellm_provider") or spec.get("provider")
                mode: str = spec.get("mode", "unknown")
                max_tokens: int = int(spec.get("max_output_tokens", 0))
                _log_config_section(
                    "FALLBACK PARSE",
                    f"  └─ {model_id} (provider: {provider}, mode: {mode}, max_tokens: {max_tokens})",
                    "DEBUG",
                )

        # Generate auto fallbacks using the same logic as auto mode
        auto_fallbacks: list[str] = generate_auto_fallbacks_from_free_models(
            free_models,
            model_type,
            clean_primary_model_id,
            fast_token_limit,
            smart_token_limit,
            strategic_token_limit,
            verbose_logging=True,
        )

        # Log what FREE_MODELS were actually selected
        if auto_fallbacks:
            _log_config_section(
                "FALLBACK PARSE",
                f"Selected {len(auto_fallbacks)} FREE_MODELS to append:",
                "DEBUG",
            )
            for i, fb in enumerate(auto_fallbacks[:10]):  # Show first 10
                _log_config_section("FALLBACK PARSE", f"  {i + 1:2d}. {fb}")
            if len(auto_fallbacks) > 10:
                _log_config_section(
                    "FALLBACK PARSE",
                    f"  ... and {len(auto_fallbacks) - 10} more",
                    "DEBUG",
                )
        else:
            _log_config_section(
                "FALLBACK PARSE",
                "No FREE_MODELS selected for appending",
                "WARN",
            )

        # Combine manual + auto fallbacks, removing duplicates while preserving order
        combined_fallbacks: list[str] = manual_fallbacks.copy()
        seen_combined: set[str] = set(manual_fallbacks)
        duplicates_found: int = 0

        for auto_fb in auto_fallbacks:
            if auto_fb not in seen_combined:
                combined_fallbacks.append(auto_fb)
                seen_combined.add(auto_fb)
            else:
                duplicates_found += 1

        _log_config_section(
            "FALLBACK PARSE",
            f"Combined fallbacks: {len(manual_fallbacks)} manual + {len(auto_fallbacks)} auto = {len(combined_fallbacks)} total",
            "DEBUG",
        )
        if duplicates_found > 0:
            _log_config_section(
                "FALLBACK PARSE",
                f"Removed {duplicates_found} duplicate FREE_MODELS already in manual list",
                "DEBUG",
            )

        return combined_fallbacks[:MAX_FALLBACKS]

    # Auto-generate fallbacks
    _log_config_section(
        "FALLBACK PARSE",
        f"Auto-generating fallbacks for {model_type}...",
        "INFO",
    )
    try:
        # Load model specs from llm_fallbacks package
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS

            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
            _log_config_section(
                "FALLBACK PARSE",
                f"Loaded {len(free_models)} free embedding models from llm_fallbacks",
                "INFO",
            )
        else:
            from llm_fallbacks.config import FREE_MODELS

            free_models = FREE_MODELS
            _log_config_section(
                "FALLBACK PARSE",
                f"Loaded {len(free_models)} free chat models from llm_fallbacks",
                "INFO",
            )

        # Show sample of what we loaded
        if free_models:
            # Randomly sample 3 models instead of always showing the first 3
            sample_count = min(3, len(free_models))
            sample_models: list[tuple[str, LiteLLMBaseModelSpec]] = random.sample(
                free_models, sample_count
            )
            _log_config_section(
                "FALLBACK PARSE",
                f"Random sample of {sample_count} FREE_MODELS loaded:",
                "DEBUG",
            )
            for model_id, spec in sample_models:
                provider: str | None = spec.get("litellm_provider") or spec.get("provider")
                mode: str = spec.get("mode", "unknown")
                max_tokens: int = int(spec.get("max_output_tokens", 0))
                _log_config_section(
                    "FALLBACK PARSE",
                    f"  └─ {model_id} (provider: {provider}, mode: {mode}, max_tokens: {max_tokens})",
                    "DEBUG",
                )

        # Use the enhanced method with verbose logging
        final_fallbacks_list: list[str] = generate_auto_fallbacks_from_free_models(
            free_models,
            model_type,
            clean_primary_model_id,
            fast_token_limit,
            smart_token_limit,
            strategic_token_limit,
            verbose_logging=True,
        )

        if final_fallbacks_list:
            _log_config_section(
                "FALLBACK PARSE",
                f"Selected {len(final_fallbacks_list)} FREE_MODELS:",
            )
            for i, fb in enumerate(final_fallbacks_list[:15]):  # Show first 15
                _log_config_section("FALLBACK PARSE", f"  {i + 1:2d}. {fb}")
            if len(final_fallbacks_list) > 15:
                _log_config_section(
                    "FALLBACK PARSE",
                    f"  ... and {len(final_fallbacks_list) - 15} more",
                )
            _log_config_section(
                "FALLBACK PARSE",
                f"Generated {len(final_fallbacks_list)} fallbacks for {model_type} (max {MAX_FALLBACKS})",
                "SUCCESS",
            )
        else:
            _log_config_section(
                "FALLBACK PARSE",
                f"No suitable fallbacks found for {model_type}",
                "WARN",
            )

        return final_fallbacks_list

    except Exception as e:
        _log_config_section(
            "FALLBACK PARSE",
            f"Failed to auto-generate fallbacks: {e.__class__.__name__}: {e}",
            "ERROR",
        )
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

    success_count: int = 0
    failure_count: int = 0

    for i, fallback_spec_str in enumerate(fallback_str_list):
        try:
            # Split into provider and model name
            if ":" not in fallback_spec_str:
                _log_config_section(
                    "PROVIDER INIT",
                    f"Invalid {llm_type_name} fallback spec '{fallback_spec_str}' (missing ':')",
                    "WARN",
                )
                failure_count += 1
                continue

            provider_name, model_name = fallback_spec_str.split(":", 1)

            if i < 3:  # Log first few initializations in detail
                _log_config_section(
                    "PROVIDER INIT",
                    f"  Initializing {llm_type_name} #{i + 1}: {fallback_spec_str}",
                    "INFO",
                )
                _log_config_section(
                    "PROVIDER INIT",
                    f"    Provider: {provider_name}",
                    "INFO",
                )
                _log_config_section(
                    "PROVIDER INIT",
                    f"    Model: {model_name}",
                    "INFO",
                )

            # Construct kwargs for the provider
            # Start with general llm_kwargs and add the specific model
            provider_kwargs: dict[str, Any] = llm_kwargs.copy()
            provider_kwargs["model"] = model_name
            provider_kwargs["verbose"] = verbose

            if i < 3:
                _log_config_section(
                    "PROVIDER INIT",
                    f"    Kwargs: {dict(provider_kwargs)}",
                    "INFO",
                )

            fallback_instance: GenericLLMProvider = GenericLLMProvider.from_provider(
                provider_name,
                chat_log=chat_log,
                **provider_kwargs,
            )
            initialized_providers.append(fallback_instance)
            success_count += 1

            if i < 3:
                _log_config_section(
                    "PROVIDER INIT",
                    "    ✅ Successfully created provider instance",
                    "INFO",
                )
                _log_config_section(
                    "PROVIDER INIT",
                    f"    Instance type: {type(fallback_instance).__name__}",
                    "INFO",
                )
        except Exception as e:
            # Log the full error message, not just the class name
            error_msg: str = str(e).strip() or "No error message provided"
            _log_config_section(
                "PROVIDER INIT",
                f"Failed to initialize {llm_type_name} fallback '{fallback_spec_str}': {e.__class__.__name__}: {error_msg}",
                "WARN",
            )

            # Always show the traceback info if DEBUG_FALLBACKS is set
            failure_count += 1
            if os.getenv("DEBUG_FALLBACKS", "").lower() in ("true", "1") or os.getenv(
                "VERBOSE", ""
            ).lower() in ("true", "1"):
                tb_str: str = traceback.format_exc()
                _log_config_section(
                    "PROVIDER INIT",
                    f"Traceback for '{fallback_spec_str}':\n{tb_str}",
                    "WARN",
                )

    # Log summary for this type
    if success_count > 0 or failure_count > 0:
        status: str = (
            "SUCCESS"
            if failure_count == 0
            else "WARN"
            if success_count > 0
            else "ERROR"
        )
        _log_config_section(
            "PROVIDER INIT",
            f"{llm_type_name.upper()}: {success_count} initialized, {failure_count} failed",
            status,
        )

    return initialized_providers


def set_llm_attributes(config_instance: Config) -> None:
    """Set LLM attributes for a config instance.

    Args:
        config_instance: The Config instance to set attributes on
    """
    _log_config_section("LLM CONFIG", "Configuring language models and fallbacks...")

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
            _log_config_section("LLM CONFIG", f"Auto-selected FAST_LLM: {config_instance.fast_llm}", "SUCCESS")
        else:
            _log_config_section("LLM CONFIG", "No FAST_LLM specified and no fallbacks available", "WARN")

    if not config_instance.smart_llm or config_instance.smart_llm.strip().lower() == "auto":
        if smart_llm_fallback_str_list:
            config_instance.smart_llm = smart_llm_fallback_str_list[0]
            _log_config_section("LLM CONFIG", f"Auto-selected SMART_LLM: {config_instance.smart_llm}", "SUCCESS")
        else:
            _log_config_section("LLM CONFIG", "No SMART_LLM specified and no fallbacks available", "WARN")

    if not config_instance.strategic_llm or config_instance.strategic_llm.strip().lower() == "auto":
        if strategic_llm_fallback_str_list:
            config_instance.strategic_llm = strategic_llm_fallback_str_list[0]
            _log_config_section("LLM CONFIG", f"Auto-selected STRATEGIC_LLM: {config_instance.strategic_llm}", "SUCCESS")
        else:
            _log_config_section("LLM CONFIG", "No STRATEGIC_LLM specified and no fallbacks available", "WARN")

    # Now parse the main LLMs (which might have been updated from fallbacks)
    # Import the Config class to access the static parse_llm method
    from gpt_researcher.config.config import Config
    config_instance.fast_llm_provider, config_instance.fast_llm_model = Config.parse_llm(config_instance.fast_llm)
    config_instance.smart_llm_provider, config_instance.smart_llm_model = Config.parse_llm(config_instance.smart_llm)
    config_instance.strategic_llm_provider, config_instance.strategic_llm_model = Config.parse_llm(config_instance.strategic_llm)

    # Log primary model configuration
    _log_config_section("LLM CONFIG", "Primary models configured:")
    _log_config_section("LLM CONFIG", f"  ├─ FAST: {config_instance.fast_llm or 'None'}")
    _log_config_section("LLM CONFIG", f"  ├─ SMART: {config_instance.smart_llm or 'None'}")
    _log_config_section("LLM CONFIG", f"  └─ STRATEGIC: {config_instance.strategic_llm or 'None'}")

    # Remove the main model from fallbacks to avoid duplication
    if config_instance.fast_llm and config_instance.fast_llm in fast_llm_fallback_str_list:
        fast_llm_fallback_str_list.remove(config_instance.fast_llm)
    if config_instance.smart_llm and config_instance.smart_llm in smart_llm_fallback_str_list:
        smart_llm_fallback_str_list.remove(config_instance.smart_llm)
    if config_instance.strategic_llm and config_instance.strategic_llm in strategic_llm_fallback_str_list:
        strategic_llm_fallback_str_list.remove(config_instance.strategic_llm)

    # Log fallback summaries
    _log_fallback_summary("fast", config_instance.fast_llm, fast_llm_fallback_str_list)
    _log_fallback_summary("smart", config_instance.smart_llm, smart_llm_fallback_str_list)
    _log_fallback_summary("strategic", config_instance.strategic_llm, strategic_llm_fallback_str_list)

    # Initialize fallback providers (use cached values if available)
    # Import the Config class to access class variables
    if not Config._fallbacks_initialized:
        _log_config_section("PROVIDERS", "Initializing fallback providers for first time...")
        Config._cached_fast_llm_fallback_providers = initialize_fallback_providers_for_type(fast_llm_fallback_str_list, "fast", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._cached_smart_llm_fallback_providers = initialize_fallback_providers_for_type(smart_llm_fallback_str_list, "smart", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._cached_strategic_llm_fallback_providers = initialize_fallback_providers_for_type(strategic_llm_fallback_str_list, "strategic", config_instance.llm_kwargs, getattr(config_instance, "chat_log", None), getattr(config_instance, "verbose", True))
        Config._fallbacks_initialized = True

        total_providers: int = len(Config._cached_fast_llm_fallback_providers) + len(Config._cached_smart_llm_fallback_providers) + len(Config._cached_strategic_llm_fallback_providers)
        _log_config_section("PROVIDERS", f"Cached {total_providers} fallback providers", "SUCCESS")
    else:
        _log_config_section("PROVIDERS", "Using cached fallback providers")

    # Assign the cached providers to this instance
    config_instance.fast_llm_fallback_providers = Config._cached_fast_llm_fallback_providers
    config_instance.smart_llm_fallback_providers = Config._cached_smart_llm_fallback_providers
    config_instance.strategic_llm_fallback_providers = Config._cached_strategic_llm_fallback_providers
