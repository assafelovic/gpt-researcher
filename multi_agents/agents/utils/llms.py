from langchain_community.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI


async def call_model(prompt: list, model: str, max_retries: int = 2, response_format: str = None, api_key: str = None) -> str:

    optional_params = {}
    if response_format == 'json':
        optional_params = {
            "response_format": {"type": "json_object"}
        }

    lc_messages = convert_openai_messages(prompt)
    response = ChatOpenAI(model=model, max_retries=max_retries, model_kwargs=optional_params, api_key=api_key).invoke(lc_messages).content
    return response