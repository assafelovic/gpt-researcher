from __future__ import annotations

from typing import Any

import json5 as json
import json_repair
from langchain_core.messages.base import BaseMessage

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion
from langchain_community.adapters.openai import convert_openai_messages
from loguru import logger


async def call_model(
    prompt: list,
    model: str,
    response_format: str | None = None,
    cfg: Config | None = None,
) -> Any | None:
    optional_params: dict[str, Any] = {}
    if str(response_format or "").casefold().strip() == "json":
        optional_params = {"response_format": {"type": "json_object"}}

    cfg = Config() if cfg is None else cfg
    lc_messages: list[BaseMessage] = convert_openai_messages(prompt)

    try:
        response: str = await create_chat_completion(
            model=model,
            messages=lc_messages,
            temperature=0,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cfg=cfg,
            # cost_callback=cost_callback,
        )

        if response_format == "json":
            try:
                cleaned_json_string: str = response.strip("```json\n")
                return json.loads(cleaned_json_string)
            except Exception as e:
                print(f"⚠️ Error in reading JSON, attempting to repair JSON : {e.__class__.__name__}: {e}")
                logger.error(f"Error in reading JSON : {e.__class__.__name__}: {e}, attempting to repair reponse: {response}")
                return json_repair.loads(response)
        else:
            return response

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e.__class__.__name__}: {e}")
