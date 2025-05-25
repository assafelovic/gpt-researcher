from __future__ import annotations

import http.client
import json
import os

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from llm_fallbacks.config import LiteLLMBaseModelSpec


def _get_litellm_models() -> dict[str, Any]:
    import importlib.util

    if importlib.util.find_spec("litellm"):
        import litellm

        return dict(litellm.model_cost)

    def _local_fallback():
        import importlib.resources

        content: str = importlib.resources.read_text(
            "litellm",
            "model_prices_and_context_window_backup.json",
        )
        return json.loads(content)

    if os.getenv("LITELLM_LOCAL_MODEL_COST_MAP", False) in {True, "True"}:
        return _local_fallback()

    try:
        conn = http.client.HTTPSConnection("raw.githubusercontent.com")
        conn.request("GET", "/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json")
        response = conn.getresponse()

        if response.status != 200:
            raise Exception(f"Request failed with status: {response.status}: {response.reason}")
        return json.loads(response.read())
    except Exception:
        return _local_fallback()


CACHED_LITELLM_MODELS: dict[str, LiteLLMBaseModelSpec] = {}


def get_litellm_models(
    *,
    test_prepend_provider: bool = False,
    use_cache: bool = True,
) -> dict[str, LiteLLMBaseModelSpec]:
    """Get all available LiteLLM models and their specifications.

    Args:
    ----
        test_prepend_provider: Prepends litellm's 'litellm_provider' to the model name. Only useful for testing.
        use_cache: Whether to use the cached LiteLLM models, or reacquire them.

    Returns:
    -------
        dict[str, Any]: Dictionary where keys are model names and values are their specifications
    """
    if CACHED_LITELLM_MODELS and use_cache:
        return CACHED_LITELLM_MODELS

    models: dict[str, LiteLLMBaseModelSpec] = {}
    for k, v in _get_litellm_models().items():
        casefold_key = model_key = str(k).casefold()
        if casefold_key == "sample_spec":
            continue

        if test_prepend_provider:
            if casefold_key.startswith(str(v["litellm_provider"]).casefold()):
                model_key = casefold_key
            else:
                model_key = f"{v['litellm_provider']}/{casefold_key}".casefold()

            model_key = (
                model_key.replace("vertex_ai-language-models", "vertex_ai")
                .replace("vertex_ai-vision-models", "vertex_ai")
                .replace("vertex_ai-mistral_models", "vertex_ai")
                .replace("fireworks_ai/accounts/fireworks/models", "fireworks_ai")
                .replace("vertex_ai-anthropic_models", "vertex_ai")
                .replace("bedrock/eu-west-3", "bedrock")
                .replace("bedrock/us-east-1", "bedrock")
                .replace("bedrock/us-west-2", "bedrock")
                .replace("vertex_ai-llama_models", "vertex_ai")
                .replace("vertex_ai-image_models", "vertex_ai")
                .replace("vertex_ai-image-models", "vertex_ai")
                .replace("vertex_ai-embedding-models", "vertex_ai")
                .replace("fireworks_ai-embedding-models", "fireworks_ai")
                .replace("vertex_ai-text-models", "vertex_ai")
                .replace("vertex_ai-code-text-models", "vertex_ai")
                .replace("vertex_ai-chat-models", "vertex_ai")
                .replace("vertex_ai-code-chat-models", "vertex_ai")
                .replace("vertex_ai-ai21_models", "vertex_ai")
                .replace("vertex_ai/vertex_ai/", "vertex_ai/")
                .replace("fireworks_ai/fireworks_ai/", "fireworks_ai/")
            )
        models[model_key] = v

    return models


def calculate_cost_per_token(
    model_spec: LiteLLMBaseModelSpec,
) -> float:
    final_cost: float = 0
    found: bool = False
    # Prioritize token-based costs first
    token_costs: list[tuple[str, str | None, float]] = [
        ("input_cost_per_token", "output_cost_per_token", 1.0),
        ("input_cost_per_token_above_128k_tokens", "output_cost_per_token_above_128k_tokens", 1.0),
        ("input_cost_per_token_batches", "output_cost_per_token_batches", 1.0),
        ("input_cost_per_token_batch_requests", None, 1.0),
        ("input_cost_per_token_cache_hit", None, 1.0),
        ("input_dbu_cost_per_token", "output_dbu_cost_per_token", 1.0),
        ("cache_creation_input_token_cost", None, 1.0),
        ("cache_read_input_token_cost", None, 1.0),
        ("input_cost_per_character", "output_cost_per_character", 4.0),  # Assuming 4 chars per token
        ("input_cost_per_character_above_128k_tokens", "output_cost_per_character_above_128k_tokens", 4.0),
        ("input_cost_per_second", "output_cost_per_second", 0.1),  # Assuming 10 tokens per second
        ("input_cost_per_audio_per_second", None, 0.1),
        ("input_cost_per_audio_per_second_above_128k_tokens", None, 0.1),
        ("input_cost_per_video_per_second", None, 0.1),
        ("input_cost_per_video_per_second_above_128k_tokens", None, 0.1),
        ("input_cost_per_audio_token", "output_cost_per_audio_token", 1.0),
        ("input_cost_per_image", "output_cost_per_image", 1.0),
        ("input_cost_per_image_above_128k_tokens", None, 1.0),
        ("input_cost_per_pixel", "output_cost_per_pixel", 1.0),
        ("input_cost_per_query", None, 1.0),
        ("input_cost_per_request", None, 1.0),
    ]

    for input_key, output_key, multiplier in token_costs:
        input_cost = cast(dict[str, Any], model_spec).get(input_key, -1)
        output_cost = (
            -1 if output_key is None else cast(dict[str, Any], model_spec).get(output_key, -1)
        )

        if isinstance(input_cost, (int, float)) and isinstance(output_cost, (int, float)):
            if input_cost >= 0:
                final_cost += input_cost * multiplier
                found = True
            if output_cost >= 0:
                final_cost += output_cost * multiplier
                found = True

    if not found:
        return -1

    return final_cost


def calculate_approx_max_tokens(
    model_spec: LiteLLMBaseModelSpec,
) -> float:
    final_total: float = 0.0
    found: bool = False

    # Define all token limit checks with their multipliers
    token_limits: list[tuple[str, float]] = [
        ("max_tokens", 1.0),
        ("max_input_tokens", 1.0),
        ("max_output_tokens", 1.0),
        ("max_audio_length_hours", 36000.0),  # 3600 sec/hr * 10 tokens/sec
        ("max_query_tokens", 1.0),
        ("max_audio_per_prompt", 1000.0),  # 1000 tokens per audio
        ("max_images_per_prompt", 1000.0),  # 1000 tokens per image
        ("max_videos_per_prompt", 2000.0),  # 2000 tokens per video
        ("max_pdf_size_mb", 1000.0),  # 1000 tokens per MB
    ]

    for limit_key, multiplier in token_limits:
        val = cast(dict[str, Any], model_spec).get(limit_key, -1)
        if isinstance(val, (int, float)) and val > 0:
            final_total += val * multiplier
            found = True

    if not found:
        return -1

    return final_total


def sort_models_by_cost_and_limits(
    models: dict[str, LiteLLMBaseModelSpec],
    free_only: bool = False,
) -> list[tuple[str, LiteLLMBaseModelSpec]]:
    """Sort models by cost (primary) and token limits (secondary).

    Args:
    ----
        models: Dictionary of model specifications. If None, will call get_litellm_models()
        free_only: If True, only return models with zero cost

    Returns:
    -------
        list of tuples mapping model names to their original specifications, sorted by cost and token limits
    """

    def _negative_one_to_inf(x: float | int) -> float | int:
        return float("inf") if x in {-1, -1.0} else x

    # Filter out ollama models and optionally filter for free models
    filtered_models: dict[str, LiteLLMBaseModelSpec] = {
        model: spec
        for model, spec in models.items()
        if not model.casefold().strip().startswith("ollama/")
        and (
            not free_only
            or all(
                cast(dict[str, Any], spec).get(key, 0) == 0
                for key in [
                    "input_cost_per_token",
                    "output_cost_per_token",
                    "input_cost_per_character",
                    "output_cost_per_character",
                    "input_cost_per_second",
                    "output_cost_per_second",
                ]
            )
        )
    }

    # Calculate costs and max tokens
    model_costs: dict[str, dict[str, float]] = {
        model: {
            "approx_cost_per_token": calculate_cost_per_token(spec),
            "approx_max_tokens": calculate_approx_max_tokens(spec),
        }
        for model, spec in filtered_models.items()
    }

    # Sort models by cost (low to high)
    # If costs are exactly the same, sort by max tokens (high to low)
    def _sort_key(
        x: tuple[str, LiteLLMBaseModelSpec],
    ) -> tuple[float, float]:
        max_tokens: float = model_costs[x[0]]["approx_max_tokens"]
        sort_value: tuple[float | int, float] = (
            _negative_one_to_inf(model_costs[x[0]]["approx_cost_per_token"]),
            float("inf") if max_tokens == -1 else -max_tokens,
        )
        return sort_value

    models_to_sort: list[tuple[str, LiteLLMBaseModelSpec]] = list(filtered_models.items())
    sorted_models: list[tuple[str, LiteLLMBaseModelSpec]] = sorted(models_to_sort, key=_sort_key)

    return sorted_models


def get_litellm_model_specs(
    *,
    test_prepend_provider: bool = False,
) -> dict[str, LiteLLMBaseModelSpec]:
    """Convert LiteLLM model specifications into dataclasses and deserialize.

    Args:
        test_prepend_provider: Whether to prepend the provider name to the model name.
            This is useful for testing purposes.

    Returns:
        dict[str, LiteLLMModelSpec]: Dictionary of model names and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models(
            test_prepend_provider=test_prepend_provider
        ).items()
    }


def get_chat_models(
    supports_audio_input: bool | None = None,
    supports_audio_output: bool | None = None,
    supports_vision: bool | None = None,
) -> dict[str, LiteLLMBaseModelSpec]:
    """Get chat-capable models, optionally filtered by cost and token limits.

    This function returns models that:
    1. Have mode set to "chat"
    2. If supports_audio_input or supports_audio_output is provided, only returns
        models that do or do not support audio input or output based on the boolean value
    3. If supports_vision is provided, only returns models that do or do not support vision based on the boolean value

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of chat models and their specifications
    """
    models = get_litellm_models()
    filtered_models: dict[str, LiteLLMBaseModelSpec] = {}

    for model_name, model_spec in models.items():
        # Check mode
        if (cast(dict[str, Any], model_spec).get("mode", "") or "").lower() != "chat":
            continue

        # Check audio input support
        if supports_audio_input is not None:
            audio_input_support = cast(dict[str, Any], model_spec).get(
                "supports_audio_input",
                False,
            )
            if bool(audio_input_support) != supports_audio_input:
                continue

        # Check audio output support
        if supports_audio_output is not None:
            audio_output_support = cast(dict[str, Any], model_spec).get(
                "supports_audio_output", False
            )
            if bool(audio_output_support) != supports_audio_output:
                continue

        # Check vision support
        if supports_vision is not None:
            vision_support = cast(dict[str, Any], model_spec).get("supports_vision", False)
            if bool(vision_support) != supports_vision:
                continue

        filtered_models[model_name] = model_spec

    return filtered_models


def get_completion_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get completion-capable models, optionally filtered by cost and token limits.

    This function returns models that have mode set to "completion"

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of completion models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip() == "completion"
    }


def get_embedding_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get embedding-capable models, optionally filtered by cost and token limits.

    This function returns models that have mode set to "embedding"

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of embedding models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip() == "embedding"
    }


def get_image_generation_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get image generation models, optionally filtered by cost.

    This function returns models that have mode set to "image_generation"

    Returns:
        dict[str, Any]: Dictionary of image generation models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip() == "image_generation"
    }


def get_audio_transcription_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get audio transcription models, optionally filtered by cost.

    This function returns models that have mode set to "audio_transcription"

    Returns:
        dict[str, Any]: Dictionary of audio transcription models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip()
        == "audio_transcription"
    }


def get_audio_speech_models() -> dict[str, Any]:
    """Get text-to-speech models, optionally filtered by cost.

    This function returns models that have mode set to "audio_speech"

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of text-to-speech models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip() == "audio_speech"
    }


def get_moderation_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get content moderation models, optionally filtered by cost.

    This function returns models that have mode set to either "moderation" or "moderations"

    Returns:
        dict[str, Any]: Dictionary of moderation models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip()
        in ["moderation", "moderations"]
    }


def get_rerank_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get reranking models, optionally filtered by cost.

    This function returns models that have mode set to "rerank"

    Returns:
        dict[str, Any]: Dictionary of reranking models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if str(cast(dict[str, Any], model_spec).get("mode", "") or "").strip() == "rerank"
    }


def get_vision_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get vision-capable models, optionally filtered by cost.

    This function returns models that support vision capabilities

    Returns:
        dict[str, Any]: Dictionary of vision-capable models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_vision")
    }


def get_function_calling_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get function-calling capable models, optionally filtered by cost.

    This function returns models that support function calling

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of function-calling models and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_function_calling")
    }


def get_parallel_function_calling_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get models that support parallel function calling, optionally filtered by cost.

    This function returns models that support parallel function calling

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of models supporting parallel function calling and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_parallel_function_calling")
    }


def get_image_input_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get models that support image input, optionally filtered by cost.

    This function returns models that support image input

    Returns:
        dict[str, Any]: Dictionary of models supporting image input and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_image_input")
    }


def get_audio_input_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get models that support audio input, optionally filtered by cost.

    This function returns models that support audio input

    Returns:
        dict[str, Any]: Dictionary of models supporting audio input and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_audio_input")
    }


def get_audio_output_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get models that support audio output, optionally filtered by cost.

    This function returns models that support audio output

    Returns:
        dict[str, Any]: Dictionary of models supporting audio output and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_audio_output")
    }


def get_pdf_input_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get models that support PDF input, optionally filtered by cost.

    This function returns models that support PDF input

    Returns:
        dict[str, Any]: Dictionary of models supporting PDF input and their specifications
    """
    return {
        model_name: model_spec
        for model_name, model_spec in get_litellm_models().items()
        if cast(dict[str, Any], model_spec).get("supports_pdf_input")
    }


def get_models() -> dict[str, LiteLLMBaseModelSpec]:
    """Get all available models.

    Returns:
        dict[str, LiteLLMBaseModelSpec]: Dictionary of all models and their specifications known to litellm
    """
    return get_litellm_models()


def get_fallback_list(
    model_type: str,
) -> list[str]:
    """Get the fallback list for a specific model type.

    Args:
    ----
        model_type: Type of model to get fallbacks for

    Returns:
    -------
        list of model names in fallback order

    Raises:
    ------
        ValueError: If model_type is not recognized
    """
    fallbacks: dict[str, list[tuple[str, LiteLLMBaseModelSpec]]] = {
        "audio_input": sort_models_by_cost_and_limits(get_audio_input_models()),
        "audio_output": sort_models_by_cost_and_limits(get_audio_output_models()),
        "audio_speech": sort_models_by_cost_and_limits(get_audio_speech_models()),
        "audio_transcription": sort_models_by_cost_and_limits(get_audio_transcription_models()),
        "chat": sort_models_by_cost_and_limits(get_chat_models()),
        "completion": sort_models_by_cost_and_limits(get_completion_models()),
        "embedding": sort_models_by_cost_and_limits(get_embedding_models()),
        "function_calling": sort_models_by_cost_and_limits(get_function_calling_models()),
        "image_generation": sort_models_by_cost_and_limits(get_image_generation_models()),
        "image_input": sort_models_by_cost_and_limits(get_image_input_models()),
        "moderation": sort_models_by_cost_and_limits(get_moderation_models()),
        "pdf_input": sort_models_by_cost_and_limits(get_pdf_input_models()),
        "rerank": sort_models_by_cost_and_limits(get_rerank_models()),
        "vision": sort_models_by_cost_and_limits(get_vision_models()),
    }

    if model_type not in fallbacks:
        raise ValueError(
            f"Unknown model type: {model_type}. Available types: {', '.join(sorted(fallbacks.keys()))}"
        )

    return [model for model, _ in fallbacks[model_type]]
