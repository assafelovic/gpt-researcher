from __future__ import annotations

import asyncio
import logging
import traceback

from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from litellm.utils import get_max_tokens

load_dotenv()


logger = logging.getLogger(__name__)


async def main():
    cfg = Config()

    try:
        provider = GenericLLMProvider(
            cfg.SMART_LLM_PROVIDER,
            model=cfg.SMART_LLM_MODEL,
            temperature=0.35,
            fallback_models=cfg.FALLBACK_MODELS,
            max_tokens=get_max_tokens(cfg.SMART_LLM_MODEL),  # type: ignore[attr-defined]
            **cfg.llm_kwargs,
        )
        response = await provider.get_chat_response(
            messages=[{"role": "user", "content": "sup?"}],
            stream=True,
        )
        print(response)
        logger.info(response)
    except Exception as e:
        logger.exception(f"Error in calling LLM: {e.__class__.__name__}: {e}")
        traceback.print_exc()


# Run the async function
asyncio.run(main())
logger.info("Done")
