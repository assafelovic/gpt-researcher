"""Helpers for the local Gemma 4 Obliterated Ollama setup."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

DEFAULT_GGUF_PATH = Path(
    "/home/xxammaxx/Schreibtisch/gemma4/llama.cpp/models/"
    "gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf"
)
DEFAULT_MODEL_NAME = "gemma4_obliterated"
DEFAULT_NUM_CTX = 2048
DEFAULT_NUM_PREDICT = 1024
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_REPEAT_PENALTY = 1.05


def build_gemma4_obliterated_modelfile(
    gguf_path: str | Path = DEFAULT_GGUF_PATH,
    *,
    num_ctx: int = DEFAULT_NUM_CTX,
    num_predict: int = DEFAULT_NUM_PREDICT,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    top_k: int = DEFAULT_TOP_K,
    repeat_penalty: float = DEFAULT_REPEAT_PENALTY,
) -> str:
    """Return a minimal Modelfile for the local Gemma 4 Obliterated GGUF."""
    resolved_path = Path(gguf_path).expanduser().resolve()
    return (
        dedent(
            f"""\
            # Local Ollama import for the Gemma 4 Obliterated GGUF checkpoint.
            # The GGUF already carries the model's prompt template, so keep
            # the Modelfile minimal and avoid overriding it here.
            FROM {resolved_path}
            PARAMETER num_ctx {num_ctx}
            PARAMETER num_predict {num_predict}
            PARAMETER temperature {temperature}
            PARAMETER top_p {top_p}
            PARAMETER top_k {top_k}
            PARAMETER repeat_penalty {repeat_penalty}
            """
        ).strip()
        + "\n"
    )
