from __future__ import annotations

import os
import re
import traceback
from typing import Any, Literal, TYPE_CHECKING

from colorama import Fore, Style

from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.llm_provider.generic.base import _SUPPORTED_PROVIDERS

if TYPE_CHECKING:
    from llm_fallbacks.config import LiteLLMBaseModelSpec

MAX_FALLBACKS: int = 25


def _log_config_section(
    section_name: str,
    message: str,
    level: str = "INFO",
) -> None:
    """Helper function for consistent config logging."""
    colors: dict[str, str] = {
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
) -> None:
    """Log a concise summary of fallback configuration."""
    if not fallbacks:
        _log_config_section("FALLBACKS", f"No fallbacks configured for {model_type.upper()}", "WARN")
        return

    display_count: int = min(len(fallbacks), max_display)
    fallback_preview: list[str] = fallbacks[:display_count]
    more_indicator: str = f" (+{len(fallbacks) - display_count} more)" if len(fallbacks) > max_display else ""

    _log_config_section(
        "FALLBACKS",
        f"{model_type.upper()}: {primary_model or 'auto'} → {display_count} fallbacks{more_indicator}"
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
        _log_config_section("FALLBACKS", f"  └─ {provider}: {model_list}")


def map_litellm_provider_to_gptr_provider(litellm_provider_name: str | None) -> str | None:
    """Maps LiteLLM provider names to GPT Researcher expected provider names."""
    if not litellm_provider_name:
        return None

    # Ensure _SUPPORTED_PROVIDERS is accessible here or pass it
    # For now, direct check against known problematic ones and GPTR supported ones

    name_lower: str = litellm_provider_name.lower()

    mapping: dict[str, str] = {
        "azure": "azure_openai",
        "azure openai": "azure_openai",
        "google": "google_genai",  # Handles cases where litellm_provider might just be "google"
        "gemini": "google_genai",  # Specifically for gemini-xyz models
        "vertex_ai": "google_vertexai",
        "vertex_ai_beta": "google_vertexai",
        "mistral": "mistralai",
    }

    if name_lower in mapping:
        return mapping[name_lower]

    # If the name (possibly after lowercasing) is already in GPTR's supported list, use it
    if name_lower in _SUPPORTED_PROVIDERS:
        return name_lower
    if litellm_provider_name in _SUPPORTED_PROVIDERS:  # Check original case too
        return litellm_provider_name

    # As a last resort, return the original name; GenericLLMProvider.from_provider will validate
    # Potentially log a warning here if a provider name isn't directly supported or mapped
    print(f"Warning: LiteLLM provider name '{litellm_provider_name}' not explicitly mapped or found in GPTR supported list. Using as is.")
    return litellm_provider_name


def generate_auto_fallbacks_from_free_models(
    free_models: list[tuple[str, "LiteLLMBaseModelSpec"]],
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

    if verbose_logging:
        _log_config_section("FREE_MODELS", f"Processing {len(free_models)} FREE_MODELS for {model_type}")
        _log_config_section("FREE_MODELS", f"Required token limit: {required_token_limit}")
        _log_config_section("FREE_MODELS", f"Primary model to exclude: '{clean_primary_model_id}'")

    # Filter models based on token limit and other criteria
    final_candidates: list[str] = []
    blacklisted_patterns: list[str] = GenericLLMProvider.MODEL_BLACKLIST
    filtered_counts: dict[str, int] = {"blacklisted": 0, "wrong_mode": 0, "insufficient_tokens": 0}

    # Track examples for detailed logging
    accepted_examples: list[tuple[str, dict]] = []
    blacklisted_examples: list[str] = []
    wrong_mode_examples: list[tuple[str, str]] = []
    insufficient_token_examples: list[tuple[str, int]] = []

    if verbose_logging:
        _log_config_section("FREE_MODELS", f"Blacklist patterns: {blacklisted_patterns}")

    # Process free models
    for model_id, spec in free_models:
        # Skip blacklisted models
        if any(
            re.search(pattern, model_id, re.IGNORECASE)
            for pattern in blacklisted_patterns
        ):
            filtered_counts["blacklisted"] += 1
            if verbose_logging and len(blacklisted_examples) < 5:
                blacklisted_examples.append(model_id)
            continue

        # Skip non-matching model types
        model_mode = spec.get("mode", "unknown")
        if (
            model_type == "embedding"
            and model_mode != "embedding"
        ):
            filtered_counts["wrong_mode"] += 1
            if verbose_logging and len(wrong_mode_examples) < 5:
                wrong_mode_examples.append((model_id, model_mode))
            continue
        elif (
            model_type in {"chat", "strategic_chat", "fast_chat"}
            and model_mode != "chat"
        ):
            filtered_counts["wrong_mode"] += 1
            if verbose_logging and len(wrong_mode_examples) < 5:
                wrong_mode_examples.append((model_id, model_mode))
            continue

        # Check token capacity for chat models
        if model_type in {"chat", "strategic_chat", "fast_chat"}:
            max_output_tokens: int = spec.get("max_output_tokens", 0)
            if max_output_tokens < required_token_limit:
                filtered_counts["insufficient_tokens"] += 1
                if verbose_logging and len(insufficient_token_examples) < 5:
                    insufficient_token_examples.append((model_id, max_output_tokens))
                continue

        # Model passed all filters
        final_candidates.append(model_id)
        if verbose_logging and len(accepted_examples) < 10:
            accepted_examples.append((model_id, dict(spec)))

    if verbose_logging:
        # Log filtering examples
        if blacklisted_examples:
            _log_config_section("FREE_MODELS", f"Blacklisted examples: {blacklisted_examples[:3]}{'...' if len(blacklisted_examples) > 3 else ''}")
        if wrong_mode_examples:
            mode_examples: list[str] = [f"{model} (mode: {mode})" for model, mode in wrong_mode_examples[:3]]
            _log_config_section("FREE_MODELS", f"Wrong mode examples: {mode_examples}{'...' if len(wrong_mode_examples) > 3 else ''}")
        if insufficient_token_examples:
            token_examples: list[str] = [f"{model} ({tokens} tokens)" for model, tokens in insufficient_token_examples[:3]]
            _log_config_section("FREE_MODELS", f"Insufficient tokens examples: {token_examples}{'...' if len(insufficient_token_examples) > 3 else ''}")

        # Log accepted examples
        if accepted_examples:
            _log_config_section("FREE_MODELS", f"Accepted {len(final_candidates)} models. Examples:")
            for model_id, spec in accepted_examples[:5]:
                provider = spec.get("litellm_provider", "unknown")
                tokens: int = spec.get("max_output_tokens", 0)
                mode: str = spec.get("mode", "unknown")
                _log_config_section("FREE_MODELS", f"  ✅ {model_id} (provider: {provider}, tokens: {tokens}, mode: {mode})")
            if len(accepted_examples) > 5:
                _log_config_section("FREE_MODELS", f"  ... and {len(final_candidates) - 5} more")

    # Remove the primary model from fallbacks if present
    if clean_primary_model_id and clean_primary_model_id.strip():
        before_count: int = len(final_candidates)
        final_candidates: list[str] = [
            model_id
            for model_id in final_candidates
            if model_id != clean_primary_model_id
        ]
        if verbose_logging and before_count != len(final_candidates):
            _log_config_section("FREE_MODELS", f"Removed primary model '{clean_primary_model_id}' from candidates")

    # Convert model IDs to correct fallback format
    formatted_fallbacks: list[str] = []
    free_models_dict = dict(free_models)
    conversion_examples: list[tuple[str, str, dict]] = []

    if verbose_logging:
        _log_config_section("FREE_MODELS", f"Converting {len(final_candidates)} candidates to fallback format...")

    for i, model_id_key in enumerate(final_candidates):
        spec: LiteLLMBaseModelSpec = free_models_dict.get(model_id_key, {})
        provider: str | None = spec.get("litellm_provider") or spec.get("provider")

        # Determine actual model name
        if "/" in model_id_key:
            # e.g. "openai/gpt-4o-mini" -> (openai, gpt-4o-mini)
            split: list[str] = model_id_key.split("/", 1)
            provider_from_key, model_name_from_key = split[0], split[1]
        elif ":" in model_id_key:
            # Already in provider:model_name format
            formatted_fallbacks.append(model_id_key)
            if verbose_logging and len(conversion_examples) < 5:
                conversion_examples.append((model_id_key, model_id_key, dict(spec)))
            continue
        else:
            provider_from_key, model_name_from_key = provider, model_id_key

        # If provider is litellm, use litellm:provider/model_name
        if provider_from_key == "litellm":
            # Try to extract the real provider and model name
            if "/" in model_name_from_key:
                real_provider, real_model = model_name_from_key.split("/", 1)
                final_format: str = f"litellm:{real_provider}/{real_model}"
                formatted_fallbacks.append(final_format)
            else:
                final_format = f"litellm:{model_name_from_key}"
                formatted_fallbacks.append(final_format)
        else:
            # Use provider:model_name
            final_format = f"{provider_from_key}:{model_name_from_key}"
            formatted_fallbacks.append(final_format)

        if verbose_logging and len(conversion_examples) < 5:
            conversion_examples.append((model_id_key, final_format, dict(spec)))

    if verbose_logging and conversion_examples:
        _log_config_section("FREE_MODELS", "Conversion examples:")
        for original, converted, spec in conversion_examples:
            provider = spec.get("litellm_provider", "unknown")
            _log_config_section("FREE_MODELS", f"  {original} → {converted} (provider: {provider})")

    # Final check for environment requirements
    pre_env_count: int = len(formatted_fallbacks)
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        formatted_fallbacks = [
            fb
            for fb in formatted_fallbacks
            if "google_vertexai" not in fb
            and "vertex_ai" not in fb
        ]
        if verbose_logging and pre_env_count != len(formatted_fallbacks):
            filtered_count: int = pre_env_count - len(formatted_fallbacks)
            _log_config_section("FREE_MODELS", f"Filtered {filtered_count} Google Vertex AI models (missing credentials)")

    final_result: list[str] = formatted_fallbacks[:MAX_FALLBACKS]

    if verbose_logging:
        _log_config_section("FREE_MODELS", f"Final result: {len(final_result)} FREE_MODELS selected (max {MAX_FALLBACKS})")
        _log_config_section("FREE_MODELS", f"Filter summary: {dict(filtered_counts)}")

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
    clean_primary_model_id: str = "" if not primary_model_id or primary_model_id.strip().lower() == "auto" else primary_model_id

    # For manual fallbacks - ALWAYS append FREE_MODELS to user-specified fallbacks
    if fallbacks_str.strip().lower() != "auto":
        raw_fallbacks: list[str] = [fb.strip() for fb in fallbacks_str.split(",") if fb.strip()]
        parsed_fallbacks: list[str] = [
            fb
            for fb in raw_fallbacks
            if not clean_primary_model_id
            or fb != clean_primary_model_id
        ]

        # Deduplicate manual fallbacks
        seen = set()
        manual_fallbacks: list[str] = [x for x in parsed_fallbacks if not (x in seen or seen.add(x))]

        if manual_fallbacks:
            _log_config_section(
                "FALLBACK PARSE",
                f"Manual fallbacks for {model_type}: {len(manual_fallbacks)} user-specified models"
            )
        elif fallbacks_str:
            _log_config_section(
                "FALLBACK PARSE",
                f"No valid manual fallbacks found for {model_type} after parsing",
                "WARN"
            )
            manual_fallbacks = []

        # Now auto-generate FREE_MODELS and append them to manual fallbacks
        _log_config_section("FALLBACK PARSE", "Auto-generating FREE_MODELS to append to manual fallbacks...")

        # Load FREE_MODELS for auto-generation
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS
            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
            _log_config_section("FALLBACK PARSE", f"Loaded {len(free_models)} free embedding models from llm_fallbacks")
        else:
            from llm_fallbacks.config import FREE_MODELS
            free_models = FREE_MODELS
            _log_config_section("FALLBACK PARSE", f"Loaded {len(free_models)} free chat models from llm_fallbacks")

        # Show sample of what we loaded
        if free_models:
            sample_models: list[tuple[str, LiteLLMBaseModelSpec]] = free_models[:3]
            _log_config_section("FALLBACK PARSE", "Sample FREE_MODELS loaded:")
            for model_id, spec in sample_models:
                provider: str | None = spec.get("litellm_provider") or spec.get("provider")
                mode: str = spec.get("mode", "unknown")
                max_tokens: int = int(spec.get("max_output_tokens", 0))
                _log_config_section("FALLBACK PARSE", f"  └─ {model_id} (provider: {provider}, mode: {mode}, max_tokens: {max_tokens})")

        # Generate auto fallbacks using the same logic as auto mode
        auto_fallbacks: list[str] = generate_auto_fallbacks_from_free_models(
            free_models, model_type, clean_primary_model_id,
            fast_token_limit, smart_token_limit, strategic_token_limit,
            verbose_logging=True
        )

        # Log what FREE_MODELS were actually selected
        if auto_fallbacks:
            _log_config_section("FALLBACK PARSE", f"Selected {len(auto_fallbacks)} FREE_MODELS to append:")
            for i, fb in enumerate(auto_fallbacks[:10]):  # Show first 10
                _log_config_section("FALLBACK PARSE", f"  {i+1:2d}. {fb}")
            if len(auto_fallbacks) > 10:
                _log_config_section("FALLBACK PARSE", f"  ... and {len(auto_fallbacks) - 10} more")
        else:
            _log_config_section("FALLBACK PARSE", "No FREE_MODELS selected for appending", "WARN")

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
            f"Combined fallbacks: {len(manual_fallbacks)} manual + {len(auto_fallbacks)} auto = {len(combined_fallbacks)} total"
        )
        if duplicates_found > 0:
            _log_config_section("FALLBACK PARSE", f"Removed {duplicates_found} duplicate FREE_MODELS already in manual list")

        return combined_fallbacks[:MAX_FALLBACKS]

    # Auto-generate fallbacks
    _log_config_section("FALLBACK PARSE", f"Auto-generating fallbacks for {model_type}...")
    try:
        # Load model specs from llm_fallbacks package
        if model_type == "embedding":
            from llm_fallbacks.config import FREE_EMBEDDING_MODELS
            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = FREE_EMBEDDING_MODELS
            _log_config_section("FALLBACK PARSE", f"Loaded {len(free_models)} free embedding models from llm_fallbacks")
        else:
            from llm_fallbacks.config import FREE_MODELS
            free_models = FREE_MODELS
            _log_config_section("FALLBACK PARSE", f"Loaded {len(free_models)} free chat models from llm_fallbacks")

        # Show sample of what we loaded
        if free_models:
            sample_models: list[tuple[str, LiteLLMBaseModelSpec]] = free_models[:3]
            _log_config_section("FALLBACK PARSE", "Sample FREE_MODELS loaded:")
            for model_id, spec in sample_models:
                provider: str | None = spec.get("litellm_provider") or spec.get("provider")
                mode: str = spec.get("mode", "unknown")
                max_tokens: int = int(spec.get("max_output_tokens", 0))
                _log_config_section("FALLBACK PARSE", f"  └─ {model_id} (provider: {provider}, mode: {mode}, max_tokens: {max_tokens})")

        # Use the enhanced method with verbose logging
        final_fallbacks_list: list[str] = generate_auto_fallbacks_from_free_models(
            free_models, model_type, clean_primary_model_id,
            fast_token_limit, smart_token_limit, strategic_token_limit,
            verbose_logging=True
        )

        if final_fallbacks_list:
            _log_config_section("FALLBACK PARSE", f"Selected {len(final_fallbacks_list)} FREE_MODELS:")
            for i, fb in enumerate(final_fallbacks_list[:15]):  # Show first 15
                _log_config_section("FALLBACK PARSE", f"  {i+1:2d}. {fb}")
            if len(final_fallbacks_list) > 15:
                _log_config_section("FALLBACK PARSE", f"  ... and {len(final_fallbacks_list) - 15} more")
            _log_config_section(
                "FALLBACK PARSE",
                f"Generated {len(final_fallbacks_list)} fallbacks for {model_type} (max {MAX_FALLBACKS})",
                "SUCCESS"
            )
        else:
            _log_config_section(
                "FALLBACK PARSE",
                f"No suitable fallbacks found for {model_type}",
                "WARN"
            )

        return final_fallbacks_list

    except Exception as e:
        _log_config_section("FALLBACK PARSE", f"Failed to auto-generate fallbacks: {e.__class__.__name__}: {e}", "ERROR")
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

    success_count = 0
    failure_count = 0

    for i, fallback_spec_str in enumerate(fallback_str_list):
        try:
            # Split into provider and model name
            if ":" not in fallback_spec_str:
                _log_config_section(
                    "PROVIDER INIT",
                    f"Invalid {llm_type_name} fallback spec '{fallback_spec_str}' (missing ':')",
                    "WARN"
                )
                failure_count += 1
                continue

            provider_name, model_name = fallback_spec_str.split(":", 1)

            if i < 3:  # Log first few initializations in detail
                _log_config_section("PROVIDER INIT", f"  Initializing {llm_type_name} #{i+1}: {fallback_spec_str}")
                _log_config_section("PROVIDER INIT", f"    Provider: {provider_name}")
                _log_config_section("PROVIDER INIT", f"    Model: {model_name}")

            # Construct kwargs for the provider
            # Start with general llm_kwargs and add the specific model
            provider_kwargs: dict[str, Any] = llm_kwargs.copy()
            provider_kwargs["model"] = model_name
            provider_kwargs["verbose"] = verbose

            if i < 3:
                _log_config_section("PROVIDER INIT", f"    Kwargs: {dict(provider_kwargs)}")

            fallback_instance: GenericLLMProvider = GenericLLMProvider.from_provider(
                provider_name,
                chat_log=chat_log,
                **provider_kwargs,
            )
            initialized_providers.append(fallback_instance)
            success_count += 1

            if i < 3:
                _log_config_section("PROVIDER INIT", "    ✅ Successfully created provider instance")
                _log_config_section("PROVIDER INIT", f"    Instance type: {type(fallback_instance).__name__}")
        except Exception as e:
            # Log the full error message, not just the class name
            error_msg = str(e).strip() if str(e).strip() else "No error message provided"
            _log_config_section(
                "PROVIDER INIT",
                f"Failed to initialize {llm_type_name} fallback '{fallback_spec_str}': {e.__class__.__name__}: {error_msg}",
                "WARN"
            )

            # Always show the traceback info if DEBUG_FALLBACKS is set
            failure_count += 1
            if os.getenv("DEBUG_FALLBACKS", "").lower() in ("true", "1") or os.getenv("VERBOSE", "").lower() in ("true", "1"):
                tb_str = traceback.format_exc()
                _log_config_section(
                    "PROVIDER INIT",
                    f"Traceback for '{fallback_spec_str}':\n{tb_str}",
                    "WARN"
                )

    # Log summary for this type
    if success_count > 0 or failure_count > 0:
        status = "SUCCESS" if failure_count == 0 else "WARN" if success_count > 0 else "ERROR"
        _log_config_section(
            "PROVIDER INIT",
            f"{llm_type_name.upper()}: {success_count} initialized, {failure_count} failed",
            status
        )

    return initialized_providers
