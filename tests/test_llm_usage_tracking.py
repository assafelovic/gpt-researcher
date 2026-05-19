import asyncio
import unittest

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider


class _Chunk:
    def __init__(self, content, usage_metadata=None, response_metadata=None):
        self.content = content
        self.usage_metadata = usage_metadata
        self.response_metadata = response_metadata or {}


class _StreamingLLM:
    async def astream(self, messages, **kwargs):
        yield _Chunk("Hello")
        yield _Chunk(
            "",
            usage_metadata={"input_tokens": 321, "output_tokens": 123},
            response_metadata={"usage": {"input_tokens": 321, "output_tokens": 123}},
        )


class TestLLMUsageTracking(unittest.TestCase):
    def test_stream_response_captures_usage_from_empty_final_chunk(self):
        provider = GenericLLMProvider(_StreamingLLM(), verbose=False)

        response = asyncio.run(provider.stream_response([{"role": "user", "content": "hi"}]))

        self.assertEqual(response, "Hello")
        self.assertEqual(
            provider.last_usage_metadata,
            {"input_tokens": 321, "output_tokens": 123},
        )
        self.assertEqual(
            provider.last_response_metadata.get("usage"),
            {"input_tokens": 321, "output_tokens": 123},
        )


if __name__ == "__main__":
    unittest.main()
