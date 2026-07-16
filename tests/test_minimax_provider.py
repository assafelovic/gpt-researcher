import asyncio
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from gpt_researcher.llm_provider.generic.base import (
    GenericLLMProvider,
    _SUPPORTED_PROVIDERS as LLM_PROVIDERS,
)
from gpt_researcher.llm_provider.minimax import (
    MINIMAX_ENDPOINTS,
    MINIMAX_MODEL_SPECS,
)
from gpt_researcher.memory.embeddings import Memory


class TestMiniMaxProvider(unittest.TestCase):
    def setUp(self):
        self._orig = {
            key: os.environ.get(key)
            for key in (
                "MINIMAX_API_KEY",
                "MINIMAX_REGION",
                "MINIMAX_BASE_URL",
                "MINIMAX_ANTHROPIC_BASE_URL",
            )
        }
        os.environ["MINIMAX_API_KEY"] = "test-key"
        os.environ["MINIMAX_REGION"] = "global_en"
        os.environ.pop("MINIMAX_BASE_URL", None)
        os.environ.pop("MINIMAX_ANTHROPIC_BASE_URL", None)

    def tearDown(self):
        for key, value in self._orig.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_provider_and_target_models_are_registered(self):
        self.assertIn("minimax", LLM_PROVIDERS)
        self.assertIn("minimax_anthropic", LLM_PROVIDERS)
        self.assertEqual(
            tuple(MINIMAX_MODEL_SPECS),
            ("MiniMax-M3", "MiniMax-M2.7"),
        )
        self.assertEqual(
            MINIMAX_MODEL_SPECS["MiniMax-M3"]["context_window"],
            1_000_000,
        )
        self.assertEqual(
            MINIMAX_MODEL_SPECS["MiniMax-M2.7"]["context_window"],
            204_800,
        )
        self.assertEqual(
            len(MINIMAX_MODEL_SPECS["MiniMax-M3"]["pricing_tiers_usd_per_million_tokens"]),
            4,
        )

    def test_openai_provider_and_embeddings_use_selected_region(self):
        for region, endpoints in MINIMAX_ENDPOINTS.items():
            os.environ["MINIMAX_REGION"] = region
            provider = GenericLLMProvider.from_provider(
                "minimax", model="MiniMax-M3", verbose=False
            )
            embeddings = Memory("minimax", "embo-01").get_embeddings()
            self.assertEqual(str(provider.llm.openai_api_base), endpoints["openai"])
            self.assertEqual(str(embeddings.openai_api_base), endpoints["openai"])

    def test_anthropic_provider_uses_selected_region(self):
        for region, endpoints in MINIMAX_ENDPOINTS.items():
            os.environ["MINIMAX_REGION"] = region
            provider = GenericLLMProvider.from_provider(
                "minimax_anthropic", model="MiniMax-M3", verbose=False
            )
            self.assertEqual(
                str(provider.llm._client.base_url).rstrip("/"),
                endpoints["anthropic"],
            )

    def test_anthropic_provider_captures_v1_messages_path(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["path"] = self.path
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "id": "msg_test",
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "text", "text": "ok"}],
                            "model": "MiniMax-M3",
                            "stop_reason": "end_turn",
                            "stop_sequence": None,
                            "usage": {"input_tokens": 1, "output_tokens": 1},
                        }
                    ).encode()
                )

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            os.environ["MINIMAX_ANTHROPIC_BASE_URL"] = (
                f"http://127.0.0.1:{server.server_port}/anthropic"
            )
            provider = GenericLLMProvider.from_provider(
                "minimax_anthropic", model="MiniMax-M3", verbose=False
            )
            response = asyncio.run(provider.llm.ainvoke("hello"))
            self.assertEqual(response.content, "ok")
            self.assertEqual(captured["path"], "/anthropic/v1/messages")
        finally:
            server.shutdown()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
