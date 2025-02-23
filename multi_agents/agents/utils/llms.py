from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any, List, cast

import json5 as json
import json_repair

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from langchain_community.adapters.openai import convert_openai_messages

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


async def call_model(
    prompt: list,
    model: str,
    response_format: str | None = None,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str] | tuple[str, list[dict[str, Any]]]:
    """Call an LLM model with the given prompt.

    Args:
        prompt: The prompt to send
        model: The model to use
        response_format: Optional response format
        cost_callback: Optional callback for cost tracking

    Returns:
        The model's response
    """
    cfg = Config()
    lc_messages = convert_openai_messages(prompt)

    try:
        provider = GenericLLMProvider(
            cfg.SMART_LLM_PROVIDER,
            model=model,
            temperature=0,
            **cfg.llm_kwargs,
        )
        response: str = await provider.get_chat_response(
            messages=lc_messages,
            stream=False,
            cost_callback=cost_callback,
        )

        if response_format == "json":
            try:
                result = json.loads(response.strip("```json\n"))
                assert isinstance(result, list)
                return cast(List[str], result)
            except Exception as e:
                logger.warning("⚠️ Error in reading JSON, attempting to repair JSON ⚠️")
                logger.exception(f"Error in reading JSON: {e.__class__.__name__}: {e}. Attempting to repair reponse: {response}")
                result = json_repair.loads(response)
                assert isinstance(result, list)
                return result
        else:
            return [response]

    except Exception as e:
        logger.exception(f"Error in calling model: {e.__class__.__name__}: {e}")
        return []
