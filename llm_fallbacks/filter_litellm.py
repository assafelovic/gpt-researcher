"""Fallback lists for different model types, sorted by cost and token limits."""

from __future__ import annotations

import json
import re

if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_fallbacks.config import LiteLLMBaseModelSpec
from llm_fallbacks.core import (
    get_audio_input_models,
    get_audio_output_models,
    get_audio_speech_models,
    get_audio_transcription_models,
    get_chat_models,
    get_completion_models,
    get_embedding_models,
    get_function_calling_models,
    get_image_generation_models,
    get_image_input_models,
    get_moderation_models,
    get_pdf_input_models,
    get_rerank_models,
    get_vision_models,
    sort_models_by_cost_and_limits,
)

# Chat Model Fallbacks
CHAT_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = sort_models_by_cost_and_limits(
    get_chat_models()
)

# Completion Model Fallbacks
COMPLETION_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_completion_models())
)

# Embedding Model Fallbacks
EMBEDDING_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_embedding_models())
)

# Image Generation Model Fallbacks
IMAGE_GENERATION_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_image_generation_models())
)

# Audio Transcription Model Fallbacks
AUDIO_TRANSCRIPTION_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_audio_transcription_models())
)

# Audio Speech Model Fallbacks
AUDIO_SPEECH_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_audio_speech_models())
)

# Moderation Model Fallbacks
MODERATION_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_moderation_models())
)

# Rerank Model Fallbacks
RERANK_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_rerank_models())
)

# Vision Model Fallbacks
VISION_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_vision_models())
)

# Function Calling Model Fallbacks
FUNCTION_CALLING_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_function_calling_models())
)

# Image Input Model Fallbacks
IMAGE_INPUT_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_image_input_models())
)

# Audio Input Model Fallbacks
AUDIO_INPUT_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_audio_input_models())
)

# Audio Output Model Fallbacks
AUDIO_OUTPUT_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_audio_output_models())
)

# PDF Input Model Fallbacks
PDF_INPUT_MODEL_PRIORITY_ORDER: list[tuple[str, LiteLLMBaseModelSpec]] = (
    sort_models_by_cost_and_limits(get_pdf_input_models())
)


import json

if __name__ == "__main__":

    def convert_floats_in_dict(d: dict) -> dict:
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = convert_floats_in_dict(v)
            elif isinstance(v, float):
                # Convert to string with many decimal places and strip trailing zeros
                float_str = f"{v:.100f}".rstrip("0")
                # If it ends with decimal point, add back one zero
                if float_str.endswith("."):
                    float_str += "0"
                result[k] = float_str
            else:
                result[k] = v
        return result

    model_priority_orders: dict[str, list[tuple[str, LiteLLMBaseModelSpec]]] = {
        "Chat Model Priority Order": CHAT_MODEL_PRIORITY_ORDER,
        "Completion Model Priority Order": COMPLETION_MODEL_PRIORITY_ORDER,
        "Embedding Model Priority Order": EMBEDDING_MODEL_PRIORITY_ORDER,
        "Image Generation Model Priority Order": IMAGE_GENERATION_MODEL_PRIORITY_ORDER,
        "Audio Transcription Model Priority Order": AUDIO_TRANSCRIPTION_MODEL_PRIORITY_ORDER,
        "Audio Speech Model Priority Order": AUDIO_SPEECH_MODEL_PRIORITY_ORDER,
        "Moderation Model Priority Order": MODERATION_MODEL_PRIORITY_ORDER,
        "Rerank Model Priority Order": RERANK_MODEL_PRIORITY_ORDER,
        "Vision Model Priority Order": VISION_MODEL_PRIORITY_ORDER,
        "Function Calling Model Priority Order": FUNCTION_CALLING_MODEL_PRIORITY_ORDER,
        "Image Input Model Priority Order": IMAGE_INPUT_MODEL_PRIORITY_ORDER,
        "Audio Input Model Priority Order": AUDIO_INPUT_MODEL_PRIORITY_ORDER,
        "Audio Output Model Priority Order": AUDIO_OUTPUT_MODEL_PRIORITY_ORDER,
        "PDF Input Model Priority Order": PDF_INPUT_MODEL_PRIORITY_ORDER,
    }
    from pathlib import Path

    model_priority_orders_path = Path(__file__).parent / "model_priority_orders.json"
    converted_orders = convert_floats_in_dict(model_priority_orders)
    json_output = json.dumps(converted_orders, indent=2)
    # Only remove quotes around values, not keys
    json_output = json.dumps(json.loads(json_output), indent=2, separators=(",", ": "))
    # Handle both cases - with and without trailing comma
    json_output = (
        json_output.replace('": "', '": ')
        .replace('",\n', ",\n")
        .replace('"\n', ",\n")
        .replace('"}', "}")
        .replace('"]', "]")
    )
    # Remove trailing comma before closing brace/bracket
    json_output = re.sub(r",(\s*[}\]])", r"\1", json_output)
    json_output = json_output.replace(": nan", ": -1").replace(": inf", ": -1")
    model_priority_orders_path.write_text(json_output)
