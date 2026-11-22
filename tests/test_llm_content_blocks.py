"""Providers that answer in content blocks (Gemini 3, thinking models) still yield text."""

import asyncio

from langchain_core.messages import AIMessage, AIMessageChunk

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

BLOCKS = [
    {"type": "thinking", "thinking": "internal"},
    {"type": "text", "text": "Hello "},
    {"type": "text", "text": "world!"},
]


class _BlockLLM:
    async def ainvoke(self, messages, **kwargs):
        return AIMessage(content=BLOCKS)

    async def astream(self, messages, **kwargs):
        yield AIMessageChunk(content=[{"type": "text", "text": "Hello "}])
        yield AIMessageChunk(content="")
        yield AIMessageChunk(content="world!")


def test_non_streamed_content_blocks_become_text():
    provider = GenericLLMProvider(_BlockLLM(), verbose=False)
    assert asyncio.run(provider.get_chat_response([], stream=False)) == "Hello world!"


def test_streamed_content_blocks_are_concatenated_once():
    provider = GenericLLMProvider(_BlockLLM(), verbose=False)
    assert asyncio.run(provider.get_chat_response([], stream=True)) == "Hello world!"
