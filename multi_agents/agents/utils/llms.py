import json_repair
from langchain_community.adapters.openai import convert_openai_messages
from langchain_core.utils.json import parse_json_markdown
from loguru import logger

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion


async def call_model(
    prompt: list,
    model: str,
    response_format: str | None = None,
):

    cfg = Config()
    lc_messages = convert_openai_messages(prompt)

    try:
        response = await create_chat_completion(
            model=model,
            messages=lc_messages,
            temperature=0,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            # cost_callback=cost_callback,
        )

        if response_format == "json":
            return parse_json_markdown(response, parser=json_repair.loads)

        return response

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e}")
