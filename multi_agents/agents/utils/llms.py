import json5 as json
import json_repair
from langchain_community.adapters.openai import convert_openai_messages

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

from loguru import logger


async def call_model(
    prompt: list,
    model: str,
    response_format: str = None,
):

    optional_params = {}
    if response_format == "json":
        optional_params = {"response_format": {"type": "json_object"}}

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
            try:
                cleaned_json_string = response.strip("```json\n")
                return json.loads(cleaned_json_string)
            except Exception as e:
                print("⚠️ Error in reading JSON, attempting to repair JSON")
                logger.error(
                    f"Error in reading JSON, attempting to repair reponse: {response}"
                )
                return json_repair.loads(response)
        else:
            return response

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e}")
