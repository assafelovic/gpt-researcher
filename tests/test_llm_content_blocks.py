import asyncio
import builtins
import importlib
import typing
import unittest
from unittest.mock import patch


def _load_provider_class():
    with (
        patch.object(builtins, "Any", typing.Any, create=True),
        patch.object(builtins, "List", typing.List, create=True),
    ):
        module = importlib.import_module(
            "gpt_researcher.llm_provider.generic.base"
        )
    return module.GenericLLMProvider


GenericLLMProvider = _load_provider_class()


class _Message:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = None
        self.response_metadata = {}


class _BlockContentLLM:
    async def ainvoke(self, messages, **kwargs):
        return _Message(
            [
                {"type": "text", "text": "Hello"},
                {"type": "metadata", "value": "ignored"},
                " world",
            ]
        )

    async def astream(self, messages, **kwargs):
        yield _Message([{"type": "text", "text": "Hello"}])
        yield _Message(["\n", {"type": "text", "text": "world"}])


class LLMContentBlockTests(unittest.TestCase):
    def test_non_streaming_content_blocks_return_text(self):
        provider = GenericLLMProvider(_BlockContentLLM(), verbose=False)

        response = asyncio.run(
            provider.get_chat_response(
                [{"role": "user", "content": "hi"}],
                stream=False,
            )
        )

        self.assertEqual(response, "Hello world")

    def test_streaming_content_blocks_are_joined(self):
        provider = GenericLLMProvider(_BlockContentLLM(), verbose=False)

        response = asyncio.run(
            provider.stream_response(
                [{"role": "user", "content": "hi"}],
            )
        )

        self.assertEqual(response, "Hello\nworld")


if __name__ == "__main__":
    unittest.main()
