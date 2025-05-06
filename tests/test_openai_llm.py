from __future__ import annotations

import asyncio
import traceback

from typing import TYPE_CHECKING

from dotenv import load_dotenv
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

load_dotenv()


async def main():
    # Example usage of get_llm function
    llm_provider = "openai"
    model = "gpt-3.5-turbo"
    temperature = 0.7
    max_tokens = 1000

    llm = GenericLLMProvider(
        f"{llm_provider}:{model}",
        fallback_models=[
            "litellm:openai/gpt-3.5-turbo",
            "openai:gpt-3.5-turbo",
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"LLM Provider: {llm_provider}, Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}")
    print("llm: ", llm)
    await test_llm(llm=llm)


async def test_llm(llm: GenericLLMProvider):
    # Test the connection with a simple query
    messages: list[BaseMessage] | list[dict[str, str]] = [{"role": "user", "content": "sup?"}]
    try:
        response = await llm.get_chat_response(messages, stream=False)
        print("LLM response:", response)
    except Exception as e:
        print(f"Error: {e.__class__.__name__}: {e}")
        traceback.print_exc()


# Run the async function
asyncio.run(main())
