"""Regression test for SIMILARITY_THRESHOLD env-var type coercion.

``ContextCompressor`` read the threshold as
``os.environ.get("SIMILARITY_THRESHOLD", 0.35)``. When the env var is
set, ``os.environ.get`` returns a **string**, which is later handed to
LangChain's ``EmbeddingsFilter`` and compared against float similarity
scores (``score >= threshold``) — raising
``TypeError: '>=' not supported between instances of 'float' and 'str'``
at query time. The default (a float) worked, so the bug only appeared
once a user customized the threshold. The value must be coerced to float.
"""

import os
import unittest
from unittest import mock

from gpt_researcher.context.compression import ContextCompressor


class SimilarityThresholdTypeTests(unittest.TestCase):
    def _make(self):
        # documents/embeddings are not touched by __init__'s threshold read.
        return ContextCompressor(documents=[], embeddings=object())

    def test_env_override_is_coerced_to_float(self):
        with mock.patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "0.5"}):
            cc = self._make()
        self.assertIsInstance(cc.similarity_threshold, float)
        self.assertEqual(cc.similarity_threshold, 0.5)
        # The original bug: a float score could not be compared to the value.
        self.assertTrue(0.6 >= cc.similarity_threshold)

    def test_default_is_float(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SIMILARITY_THRESHOLD", None)
            cc = self._make()
        self.assertIsInstance(cc.similarity_threshold, float)
        self.assertEqual(cc.similarity_threshold, 0.35)


if __name__ == "__main__":
    unittest.main()
