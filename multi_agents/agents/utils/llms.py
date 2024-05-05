from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI


def call_model(prompt: list, model: str, max_retries: int = 2, response_format: str = None) -> str:

    optional_params = {}
    if response_format == 'json':
        optional_params = {
            "response_format": {"type": "json_object"}
        }

    lc_messages = convert_openai_messages(prompt)
    response = ChatOpenAI(model=model, max_retries=max_retries, model_kwargs=optional_params).invoke(lc_messages).content
    return response