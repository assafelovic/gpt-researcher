#!/usr/bin/env python3
"""Create and smoke-test the local Gemma 4 Obliterated Ollama model."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gpt_researcher.utils.local_llm import resolve_ollama_base_url
from gpt_researcher.utils.ollama_setup import (
    DEFAULT_GGUF_PATH,
    DEFAULT_MODEL_NAME,
    DEFAULT_NUM_CTX,
    DEFAULT_NUM_PREDICT,
    DEFAULT_REPEAT_PENALTY,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    DEFAULT_TOP_P,
    build_gemma4_obliterated_modelfile,
)


def _repo_root() -> Path:
    return REPO_ROOT


def _write_modelfile(
    output_path: Path,
    *,
    gguf_path: Path,
    num_ctx: int,
    num_predict: int,
    temperature: float,
    top_p: float,
    top_k: int,
    repeat_penalty: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_gemma4_obliterated_modelfile(
            gguf_path=gguf_path,
            num_ctx=num_ctx,
            num_predict=num_predict,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
        ),
        encoding="utf-8",
    )


def _run_ollama(
    command: list[str], *, ollama_host: str, dry_run: bool, capture: bool = False
) -> subprocess.CompletedProcess[str] | None:
    printable = " ".join(command)
    print(f"$ OLLAMA_HOST={ollama_host} {printable}")
    if dry_run:
        return None

    env = os.environ.copy()
    env["OLLAMA_HOST"] = ollama_host
    if capture:
        return subprocess.run(command, check=True, env=env, text=True, capture_output=True)
    return subprocess.run(command, check=True, env=env, text=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the gemma4_obliterated Ollama model from the local GGUF checkpoint."
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL_NAME,
        help="Ollama model name to create.",
    )
    parser.add_argument(
        "--gguf",
        default=str(DEFAULT_GGUF_PATH),
        help="Absolute or relative path to the Gemma 4 Obliterated GGUF file.",
    )
    parser.add_argument(
        "--ollama-host",
        default=resolve_ollama_base_url(),
        help="Ollama API base URL, for example http://127.0.0.1:11434.",
    )
    parser.add_argument(
        "--output-modelfile",
        default=str(_repo_root() / ".generated" / "ollama" / "Modelfile.gemma4_obliterated"),
        help="Where to write the generated Modelfile.",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=DEFAULT_NUM_CTX,
        help="Context window to bake into the model.",
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=DEFAULT_NUM_PREDICT,
        help="Maximum generated tokens to bake into the model.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Default temperature baked into the model.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=DEFAULT_TOP_P,
        help="Default nucleus sampling cutoff baked into the model.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Default top-k baked into the model.",
    )
    parser.add_argument(
        "--repeat-penalty",
        type=float,
        default=DEFAULT_REPEAT_PENALTY,
        help="Default repetition penalty baked into the model.",
    )
    parser.add_argument(
        "--smoke-test-prompt",
        default="Reply with one short sentence confirming the model is ready.",
        help="Prompt used for the post-create smoke test.",
    )
    parser.add_argument(
        "--skip-create",
        action="store_true",
        help="Only write the Modelfile, do not call ollama create.",
    )
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="Skip the post-create ollama run smoke test.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    gguf_path = Path(args.gguf).expanduser()
    if not gguf_path.exists():
        print(f"Missing GGUF file: {gguf_path}", file=sys.stderr)
        return 1

    output_modelfile = Path(args.output_modelfile).expanduser()
    _write_modelfile(
        output_modelfile,
        gguf_path=gguf_path,
        num_ctx=args.num_ctx,
        num_predict=args.num_predict,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        repeat_penalty=args.repeat_penalty,
    )
    print(f"Wrote Modelfile to {output_modelfile}")

    if args.skip_create:
        return 0

    create_command = [
        "ollama",
        "create",
        args.model_name,
        "-f",
        str(output_modelfile),
    ]
    _run_ollama(create_command, ollama_host=args.ollama_host, dry_run=args.dry_run)

    if args.skip_smoke_test:
        print(f"Model '{args.model_name}' is ready.")
    else:
        smoke_command = [
            "ollama",
            "run",
            args.model_name,
            args.smoke_test_prompt,
        ]
        print(f"Smoke test prompt: {args.smoke_test_prompt}")
        try:
            result = _run_ollama(
                smoke_command, ollama_host=args.ollama_host, dry_run=args.dry_run, capture=True
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            if stderr:
                print(stderr, file=sys.stderr)
            if "system memory" in stderr or "available" in stderr:
                print(
                    "Hint: stop the large local llama.cpp server on 8081 or free RAM, then rerun the smoke test.",
                    file=sys.stderr,
                )
            raise
        else:
            if result and result.stdout:
                print(result.stdout.strip())

    print("")
    print("Use these GPT Researcher settings:")
    print(f"OLLAMA_BASE_URL={args.ollama_host}")
    print(f"FAST_LLM=ollama:{args.model_name}")
    print(f"SMART_LLM=ollama:{args.model_name}")
    print(f"STRATEGIC_LLM=ollama:{args.model_name}")
    print("EMBEDDING=ollama:nomic-embed-text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
