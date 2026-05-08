#!/usr/bin/env python3
"""
llama.cpp-native speculative decoding runner for Gemma 4 GGUF models.

This variant works directly with the local llama.cpp setup:
- target model is loaded via llama-server from a GGUF file or Hugging Face repo
- draft model is loaded via llama-server from a GGUF file or Hugging Face repo
- if no suitable local draft model is found, the script falls back to
  llama.cpp's draftless n-gram speculative decoding
- prompts are sent to /completion as raw text, so no chat template is applied
- speculative acceptance stats are parsed from llama-server logs and printed

The script intentionally avoids transformers, accelerate, bitsandbytes, or any
other Python inference stack. It drives llama.cpp directly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence


def default_llama_cpp_root() -> Path:
    env_root = os.environ.get("LLAMA_CPP_ROOT")
    if env_root:
        return Path(env_root).expanduser()

    local_root = Path("/home/xxammaxx/Schreibtisch/gemma4/llama.cpp")
    if local_root.exists():
        return local_root

    repo_root = Path(__file__).resolve().parents[1] / "llama.cpp"
    return repo_root


DEFAULT_LLAMA_CPP_ROOT = default_llama_cpp_root()
DEFAULT_SERVER_PATH = os.environ.get(
    "LLAMA_SERVER_PATH",
    str(DEFAULT_LLAMA_CPP_ROOT / "build/bin/llama-server"),
)
DEFAULT_TARGET_MODEL = os.environ.get(
    "TARGET_MODEL",
    str(DEFAULT_LLAMA_CPP_ROOT / "models/gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf"),
)
DEFAULT_PORT = int(os.environ.get("LLAMA_PORT", "8091"))
DEFAULT_CONTEXT_LENGTH = int(os.environ.get("LLAMA_CONTEXT_LENGTH", "4096"))
DEFAULT_THREADS = int(os.environ.get("LLAMA_THREADS", "8"))
DEFAULT_PARALLEL = int(os.environ.get("LLAMA_PARALLEL", "1"))
DEFAULT_GPU_LAYERS = int(os.environ.get("LLAMA_N_GPU_LAYERS", "999"))
DEFAULT_DRAFT_MIN = int(os.environ.get("LLAMA_DRAFT_MIN", "0"))
DEFAULT_DRAFT_MAX = int(os.environ.get("LLAMA_DRAFT_MAX", "8"))
DEFAULT_BENCHMARK_TOKENS = int(os.environ.get("LLAMA_BENCHMARK_TOKENS", "64"))
DEFAULT_MAX_NEW_TOKENS = int(os.environ.get("LLAMA_MAX_NEW_TOKENS", "256"))
DEFAULT_TEMPERATURE = float(os.environ.get("LLAMA_TEMPERATURE", "0.0"))
DEFAULT_TOP_P = float(os.environ.get("LLAMA_TOP_P", "1.0"))
DEFAULT_SPEC_NGRAM_SIZE_N = int(os.environ.get("LLAMA_SPEC_NGRAM_SIZE_N", "24"))
DEFAULT_SPEC_NGRAM_SIZE_M = int(os.environ.get("LLAMA_SPEC_NGRAM_SIZE_M", "48"))
DEFAULT_SPEC_NGRAM_MIN_HITS = int(os.environ.get("LLAMA_SPEC_NGRAM_MIN_HITS", "1"))
DEFAULT_STARTUP_TIMEOUT = int(os.environ.get("LLAMA_STARTUP_TIMEOUT", "900"))
DEFAULT_REQUEST_TIMEOUT = int(os.environ.get("LLAMA_REQUEST_TIMEOUT", "600"))
DEFAULT_HOST = os.environ.get("LLAMA_HOST", "127.0.0.1")
DEFAULT_ALIAS = os.environ.get("LLAMA_ALIAS", "gemma4-obliterated-gguf")

DRAFT_HINTS = (
    "draft",
    "abliterated",
    "abliterat",
    "abliterated",
    "uncensored",
    "unfiltered",
    "obliterated",
    "heretic",
    "e2b",
    "e4b",
)


@dataclass(frozen=True)
class ModelSource:
    kind: str
    value: str


@dataclass(frozen=True)
class SpeculativePlan:
    temperature: float
    top_p: float
    draft_min: int
    draft_max: int
    spec_type: str | None
    spec_ngram_size_n: int
    spec_ngram_size_m: int
    spec_ngram_min_hits: int


@dataclass(frozen=True)
class AcceptanceStats:
    acceptance_rate: float
    accepted_tokens: int
    generated_tokens: int
    raw_line: str


ACCEPTANCE_LINE_RE = re.compile(
    r"draft acceptance rate\s*=\s*([0-9]*\.?[0-9]+)\s*"
    r"\(\s*(\d+)\s+accepted\s*/\s*(\d+)\s+generated\s*\)",
    re.IGNORECASE,
)
GEN_ACC_STATS_RE = re.compile(
    r"#gen tokens\s*=\s*(\d+),\s*#acc tokens\s*=\s*(\d+)",
    re.IGNORECASE,
)


def human_size(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def resolve_server_path(candidate: str) -> str:
    path = Path(candidate).expanduser()
    if path.exists():
        return str(path.resolve())

    found = shutil.which(candidate)
    if found:
        return found

    raise FileNotFoundError(
        f"Could not find llama-server at {candidate!r}. "
        "Set LLAMA_SERVER_PATH or pass --server-path explicitly."
    )


def normalize_model_reference(ref: str) -> ModelSource:
    candidate = ref.strip()
    if not candidate:
        raise ValueError("Empty model reference.")
    if candidate.lower() == "auto":
        raise ValueError("auto must be handled separately.")
    if candidate.lower() == "none":
        raise ValueError("none must be handled separately.")

    path = Path(candidate).expanduser()
    if path.exists():
        if path.is_dir():
            raise ValueError(
                f"{candidate} points to a directory. Pass the GGUF file itself."
            )
        return ModelSource("local", str(path.resolve()))

    if candidate.startswith(("/", "./", "../", "~")):
        raise FileNotFoundError(f"Local model path {candidate!r} does not exist.")

    if "/" in candidate:
        return ModelSource("hf", candidate)

    raise FileNotFoundError(
        f"Could not resolve model reference {candidate!r}. "
        "Use an absolute/relative GGUF path or a Hugging Face repo such as "
        "'owner/model[:quant]'."
    )


def draft_candidate_score(candidate: Path) -> tuple[int, int, str]:
    name = candidate.name.lower()
    score = 0

    if "draft" in name:
        score += 1000
    for marker in DRAFT_HINTS:
        if marker in name:
            score += 100
    if "q4" in name:
        score += 10
    if "q5" in name or "q6" in name or "q8" in name:
        score += 5
    if "vocab" in name:
        score -= 10000

    size = candidate.stat().st_size
    return (-score, size, name)


def discover_local_draft_model(
    target_model: Path,
    search_roots: Sequence[Path],
    *,
    strict_smaller: bool,
) -> Path | None:
    target_real = target_model.resolve()
    target_size = target_model.stat().st_size
    target_stem = target_model.stem.lower()

    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in search_roots:
        if not root.exists():
            continue
        for gguf in root.glob("*.gguf"):
            try:
                resolved = gguf.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved == target_real:
                continue
            if gguf.name.lower().startswith(target_stem):
                continue
            if "vocab" in gguf.name.lower():
                continue
            candidates.append(gguf)

    if not candidates:
        return None

    ordered = sorted(candidates, key=draft_candidate_score)
    chosen = ordered[0]
    if strict_smaller and chosen.stat().st_size >= target_size:
        return None
    return chosen


def resolve_target_source(ref: str) -> ModelSource:
    candidate = ref.strip()
    if candidate.lower() == "auto":
        candidate = DEFAULT_TARGET_MODEL
    return normalize_model_reference(candidate)


def resolve_draft_source(
    ref: str,
    target_source: ModelSource,
    *,
    strict_smaller: bool,
) -> ModelSource | None:
    candidate = ref.strip()
    if candidate.lower() == "none":
        return None
    if candidate.lower() != "auto":
        return normalize_model_reference(candidate)

    if target_source.kind == "local":
        target_path = Path(target_source.value)
        models_dir = target_path.parent
        roots = [models_dir, DEFAULT_LLAMA_CPP_ROOT / "models"]
        local_draft = discover_local_draft_model(
            target_path,
            roots,
            strict_smaller=strict_smaller,
        )
        if local_draft is not None:
            return ModelSource("local", str(local_draft.resolve()))

    return None


def build_raw_prompt(user_prompt: str, system_prompt: str | None = None) -> str:
    parts: list[str] = []
    if system_prompt:
        parts.append("System instruction:\n" + system_prompt.strip())
    parts.append("User request:\n" + user_prompt.strip())
    parts.append("Assistant:")
    return "\n\n".join(parts)


def build_server_command(
    *,
    server_path: str,
    target_source: ModelSource,
    draft_source: ModelSource | None,
    plan: SpeculativePlan,
    host: str,
    port: int,
    context_length: int,
    threads: int,
    parallel: int,
    gpu_layers: int,
    ctk: str,
    ctv: str,
    flash_attn: str,
    alias: str,
) -> list[str]:
    cmd = [server_path]

    if target_source.kind == "local":
        cmd.extend(["-m", target_source.value])
    else:
        cmd.extend(["-hf", target_source.value])

    if draft_source is not None:
        if draft_source.kind == "local":
            cmd.extend(["-md", draft_source.value])
        else:
            cmd.extend(["-hfd", draft_source.value])
    else:
        cmd.extend(
            [
                "--spec-type",
                plan.spec_type or "ngram-mod",
                "--spec-ngram-size-n",
                str(plan.spec_ngram_size_n),
                "--spec-ngram-size-m",
                str(plan.spec_ngram_size_m),
                "--spec-ngram-min-hits",
                str(plan.spec_ngram_min_hits),
            ]
        )

    cmd.extend(
        [
            "--draft-min",
            str(plan.draft_min),
            "--draft-max",
            str(plan.draft_max),
            "--host",
            host,
            "--port",
            str(port),
            "-c",
            str(context_length),
            "-np",
            str(parallel),
            "--threads",
            str(threads),
            "-ngl",
            str(gpu_layers),
            "-ctk",
            ctk,
            "-ctv",
            ctv,
            "--flash-attn",
            flash_attn,
            "--alias",
            alias,
        ]
    )
    return cmd


def extract_acceptance_stats(lines: Sequence[str]) -> AcceptanceStats | None:
    text = "\n".join(lines)

    match = None
    for candidate in ACCEPTANCE_LINE_RE.finditer(text):
        match = candidate
    if match is not None:
        accepted = int(match.group(2))
        generated = int(match.group(3))
        rate = float(match.group(1))
        return AcceptanceStats(rate, accepted, generated, match.group(0))

    match = None
    for candidate in GEN_ACC_STATS_RE.finditer(text):
        match = candidate
    if match is not None:
        generated = int(match.group(1))
        accepted = int(match.group(2))
        rate = accepted / generated if generated else 0.0
        return AcceptanceStats(rate, accepted, generated, match.group(0))

    return None


def tune_plan(plan: SpeculativePlan, acceptance_rate: float) -> SpeculativePlan:
    """Make speculative decoding more conservative when acceptance is low."""

    draft_min = max(0, plan.draft_min - 1) if plan.draft_min > 0 else 0
    draft_max = max(2, plan.draft_max - 2) if plan.draft_max > 2 else plan.draft_max
    temperature = plan.temperature
    top_p = plan.top_p

    if temperature > 0.0:
        temperature = max(0.0, temperature - 0.05)
    if top_p < 1.0:
        top_p = max(0.75, top_p - 0.05)

    if acceptance_rate >= 0.70:
        return plan

    return replace(
        plan,
        temperature=temperature,
        top_p=top_p,
        draft_min=draft_min,
        draft_max=draft_max,
    )


class ManagedLlamaServer:
    def __init__(
        self,
        command: list[str],
        *,
        base_url: str,
        startup_timeout: int,
        request_timeout: int,
        show_server_logs: bool,
    ) -> None:
        self.command = command
        self.base_url = base_url.rstrip("/")
        self.startup_timeout = startup_timeout
        self.request_timeout = request_timeout
        self.show_server_logs = show_server_logs
        self.proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._log_lock = threading.Lock()
        self._logs: list[str] = []

    def __enter__(self) -> "ManagedLlamaServer":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self.proc is not None:
            return

        env = os.environ.copy()
        build_dir = str(Path(self.command[0]).expanduser().resolve().parent)
        ld_path = env.get("LD_LIBRARY_PATH")
        env["LD_LIBRARY_PATH"] = (
            build_dir if not ld_path else build_dir + ":" + ld_path
        )

        print("Starting llama-server with:")
        print("  " + shlex.join(self.command))

        self.proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        self._reader = threading.Thread(target=self._drain_logs, daemon=True)
        self._reader.start()
        self._wait_until_healthy()

    def _drain_logs(self) -> None:
        assert self.proc is not None
        assert self.proc.stdout is not None

        for line in self.proc.stdout:
            stripped = line.rstrip("\n")
            with self._log_lock:
                self._logs.append(stripped)
            if self.show_server_logs:
                print(f"[llama-server] {stripped}", flush=True)

    def _wait_until_healthy(self) -> None:
        deadline = time.monotonic() + float(self.startup_timeout)
        health_paths = ("/health", "/v1/health")

        while time.monotonic() < deadline:
            if self.proc is not None and self.proc.poll() is not None:
                recent = "\n".join(self.tail_logs(40))
                raise RuntimeError(
                    "llama-server exited before it became healthy.\n"
                    f"Command: {shlex.join(self.command)}\n"
                    f"Recent logs:\n{recent}"
                )

            for path in health_paths:
                try:
                    req = urllib.request.Request(self.base_url + path, method="GET")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            print(f"Server healthy at {self.base_url}")
                            return
                except urllib.error.HTTPError as exc:
                    if exc.code != 503:
                        continue
                except urllib.error.URLError:
                    continue
            time.sleep(0.5)

        recent = "\n".join(self.tail_logs(40))
        raise TimeoutError(
            f"Timed out waiting for llama-server to become healthy at {self.base_url}.\n"
            f"Command: {shlex.join(self.command)}\n"
            f"Recent logs:\n{recent}"
        )

    def snapshot_logs(self) -> list[str]:
        with self._log_lock:
            return list(self._logs)

    def tail_logs(self, count: int = 20) -> list[str]:
        with self._log_lock:
            return self._logs[-count:]

    def logs_since(self, index: int) -> list[str]:
        with self._log_lock:
            return self._logs[index:]

    def completion(
        self,
        *,
        prompt: str,
        n_predict: int,
        temperature: float,
        top_p: float,
        cache_prompt: bool = True,
    ) -> dict:
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
            "top_p": top_p,
            "cache_prompt": cache_prompt,
        }

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/completion",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"llama-server completion failed with HTTP {exc.code}: {exc.reason}\n"
                f"{detail}"
            ) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse completion response as JSON: {raw}") from exc

    def wait_for_stats(
        self,
        *,
        start_index: int,
        timeout: float,
    ) -> AcceptanceStats | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            stats = extract_acceptance_stats(self.logs_since(start_index))
            if stats is not None:
                return stats
            if self.proc is not None and self.proc.poll() is not None:
                break
            time.sleep(0.2)
        return extract_acceptance_stats(self.logs_since(start_index))

    def stop(self) -> None:
        if self.proc is None:
            return

        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)

        if self._reader is not None and self._reader.is_alive():
            self._reader.join(timeout=2)

        self.proc = None
        self._reader = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gemma 4 GGUF speculative decoding runner using llama.cpp directly.",
        epilog=(
            "Examples:\n"
            "  scripts/speculative_gemma4_gguf.py\n"
            "  scripts/speculative_gemma4_gguf.py --draft-model none\n"
            "  scripts/speculative_gemma4_gguf.py --draft-model DuoNeural/Gemma-4-E2B-Abliterated-GGUF:Q4_K_M\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--server-path",
        default=DEFAULT_SERVER_PATH,
        help="Path to llama-server or a name resolvable via PATH.",
    )
    parser.add_argument(
        "--target-model",
        default=DEFAULT_TARGET_MODEL,
        help=(
            "Target GGUF path or Hugging Face repo. Use 'auto' to keep the local "
            "default target."
        ),
    )
    parser.add_argument(
        "--draft-model",
        default="auto",
        help=(
            "Draft GGUF path or Hugging Face repo. Use 'auto' to discover a local "
            "candidate, or 'none' to force draftless n-gram speculation."
        ),
    )
    parser.add_argument(
        "--strict-smaller-draft",
        action="store_true",
        help="Reject local draft candidates that are not smaller than the target.",
    )
    parser.add_argument(
        "--alias",
        default=DEFAULT_ALIAS,
        help="llama-server model alias for UI and API responses.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Host to bind the temporary llama-server to.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to bind the temporary llama-server to.",
    )
    parser.add_argument(
        "-c",
        "--context-length",
        type=int,
        default=DEFAULT_CONTEXT_LENGTH,
        help="Context length passed to llama-server.",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        help="CPU thread count passed to llama-server.",
    )
    parser.add_argument(
        "-np",
        "--parallel",
        type=int,
        default=DEFAULT_PARALLEL,
        help="Number of concurrent slots passed to llama-server.",
    )
    parser.add_argument(
        "-ngl",
        "--n-gpu-layers",
        type=int,
        default=DEFAULT_GPU_LAYERS,
        help="Number of layers offloaded to the GPU.",
    )
    parser.add_argument(
        "--ctk",
        default="f32",
        help="KV cache type for keys.",
    )
    parser.add_argument(
        "--ctv",
        default="f32",
        help="KV cache type for values.",
    )
    parser.add_argument(
        "--flash-attn",
        choices=("on", "off", "auto"),
        default="off",
        help="Flash Attention setting forwarded to llama-server.",
    )
    parser.add_argument(
        "--prompt",
        default="Explain speculative decoding and why draft tokens can speed up inference.",
        help="Raw user prompt. No chat template is applied.",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Optional raw system instruction to prepend to the prompt.",
    )
    parser.add_argument(
        "--benchmark-new-tokens",
        type=int,
        default=DEFAULT_BENCHMARK_TOKENS,
        help="Number of new tokens to use for the speculative benchmark run.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=DEFAULT_MAX_NEW_TOKENS,
        help="Number of new tokens to generate in the final run.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Completion temperature. Lower values usually improve acceptance.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=DEFAULT_TOP_P,
        help="Completion top_p. Lower values usually improve acceptance.",
    )
    parser.add_argument(
        "--acceptance-target",
        type=float,
        default=0.70,
        help="Desired speculative acceptance rate.",
    )
    parser.add_argument(
        "--draft-min",
        type=int,
        default=DEFAULT_DRAFT_MIN,
        help="Minimum number of draft tokens per speculative step.",
    )
    parser.add_argument(
        "--draft-max",
        type=int,
        default=DEFAULT_DRAFT_MAX,
        help="Maximum number of draft tokens per speculative step.",
    )
    parser.add_argument(
        "--spec-type",
        choices=("ngram-cache", "ngram-simple", "ngram-map-k", "ngram-map-k4v", "ngram-mod"),
        default="ngram-mod",
        help="Draftless speculative decoding implementation to use if no draft model is available.",
    )
    parser.add_argument(
        "--spec-ngram-size-n",
        type=int,
        default=DEFAULT_SPEC_NGRAM_SIZE_N,
        help="N-gram lookup size used by draftless speculative decoding.",
    )
    parser.add_argument(
        "--spec-ngram-size-m",
        type=int,
        default=DEFAULT_SPEC_NGRAM_SIZE_M,
        help="N-gram draft size used by draftless speculative decoding.",
    )
    parser.add_argument(
        "--spec-ngram-min-hits",
        type=int,
        default=DEFAULT_SPEC_NGRAM_MIN_HITS,
        help="Minimum hits for the n-gram map speculative decoder.",
    )
    parser.add_argument(
        "--startup-timeout",
        type=int,
        default=DEFAULT_STARTUP_TIMEOUT,
        help="Seconds to wait for llama-server to become healthy.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT,
        help="Seconds to wait for each completion request.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Maximum number of tuning trials before giving up.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command and exit without starting llama-server.",
    )
    parser.add_argument(
        "--show-server-logs",
        action="store_true",
        help="Stream llama-server logs while the runner is active.",
    )
    return parser.parse_args()


def print_model_summary(
    *,
    target_source: ModelSource,
    draft_source: ModelSource | None,
    plan: SpeculativePlan,
    target_model: Path | None,
) -> None:
    print(f"Target model: {target_source.kind} -> {target_source.value}")
    if target_model is not None and target_model.exists():
        print(f"Target size:   {human_size(target_model.stat().st_size)}")

    if draft_source is None:
        print(
            "Draft model:   none (using draftless speculative decoding via "
            f"{plan.spec_type})"
        )
    else:
        print(f"Draft model:   {draft_source.kind} -> {draft_source.value}")
        if draft_source.kind == "local":
            draft_path = Path(draft_source.value)
            if draft_path.exists():
                print(f"Draft size:    {human_size(draft_path.stat().st_size)}")

    print(
        "Draft tuning:   "
        f"draft_min={plan.draft_min}, draft_max={plan.draft_max}, "
        f"temperature={plan.temperature:.2f}, top_p={plan.top_p:.2f}"
    )


def print_command(command: Sequence[str]) -> None:
    print("Resolved llama-server command:")
    print("  " + shlex.join(command))


def run() -> int:
    args = parse_args()

    server_path = resolve_server_path(args.server_path)
    target_source = resolve_target_source(args.target_model)

    target_model_path = (
        Path(target_source.value)
        if target_source.kind == "local"
        else None
    )

    draft_source = resolve_draft_source(
        args.draft_model,
        target_source,
        strict_smaller=args.strict_smaller_draft,
    )

    if draft_source is None:
        print(
            "No draft GGUF was selected; llama.cpp will use draftless speculative "
            f"decoding via {args.spec_type}."
        )
    elif draft_source.kind == "local" and target_model_path is not None:
            draft_path = Path(draft_source.value)
            if draft_path.exists():
                target_size = target_model_path.stat().st_size
                draft_size = draft_path.stat().st_size
                if draft_size >= target_size:
                    print(
                        "Warning: the selected local draft is not smaller than the target. "
                        "It should still work, but the speedup may be modest."
                    )

    draft_min = args.draft_min
    draft_max = args.draft_max
    if (
        draft_source is None
        and draft_min == DEFAULT_DRAFT_MIN
        and draft_max == DEFAULT_DRAFT_MAX
    ):
        draft_min = 48
        draft_max = 64

    plan = SpeculativePlan(
        temperature=args.temperature,
        top_p=args.top_p,
        draft_min=draft_min,
        draft_max=draft_max,
        spec_type=args.spec_type if draft_source is None else None,
        spec_ngram_size_n=args.spec_ngram_size_n,
        spec_ngram_size_m=args.spec_ngram_size_m,
        spec_ngram_min_hits=args.spec_ngram_min_hits,
    )

    prompt = build_raw_prompt(args.prompt, args.system)

    print_model_summary(
        target_source=target_source,
        draft_source=draft_source,
        plan=plan,
        target_model=target_model_path,
    )

    command = build_server_command(
        server_path=server_path,
        target_source=target_source,
        draft_source=draft_source,
        plan=plan,
        host=args.host,
        port=args.port,
        context_length=args.context_length,
        threads=args.threads,
        parallel=args.parallel,
        gpu_layers=args.n_gpu_layers,
        ctk=args.ctk,
        ctv=args.ctv,
        flash_attn=args.flash_attn,
        alias=args.alias,
    )

    print_command(command)

    if args.dry_run:
        return 0

    base_url = f"http://{args.host}:{args.port}"

    current_plan = plan
    acceptance_target = args.acceptance_target

    for trial in range(1, max(1, args.trials) + 1):
        command = build_server_command(
            server_path=server_path,
            target_source=target_source,
            draft_source=draft_source,
            plan=current_plan,
            host=args.host,
            port=args.port,
            context_length=args.context_length,
            threads=args.threads,
            parallel=args.parallel,
            gpu_layers=args.n_gpu_layers,
            ctk=args.ctk,
            ctv=args.ctv,
            flash_attn=args.flash_attn,
            alias=args.alias,
        )

        with ManagedLlamaServer(
            command,
            base_url=base_url,
            startup_timeout=args.startup_timeout,
            request_timeout=args.request_timeout,
            show_server_logs=args.show_server_logs,
        ) as server:
            print(
                f"Trial {trial}/{max(1, args.trials)}: benchmarking speculative decoding "
                f"with n_predict={args.benchmark_new_tokens}"
            )
            benchmark_start = len(server.snapshot_logs())
            _benchmark_response = server.completion(
                prompt=prompt,
                n_predict=args.benchmark_new_tokens,
                temperature=current_plan.temperature,
                top_p=current_plan.top_p,
                cache_prompt=True,
            )
            benchmark_stats = server.wait_for_stats(
                start_index=benchmark_start,
                timeout=min(float(args.request_timeout), 120.0),
            )

            if benchmark_stats is None:
                recent = "\n".join(server.tail_logs(40))
                raise RuntimeError(
                    "Could not parse speculative acceptance stats from llama-server logs.\n"
                    f"Recent logs:\n{recent}"
                )

            print(
                "Benchmark acceptance: "
                f"{benchmark_stats.acceptance_rate * 100.0:.1f}% "
                f"({benchmark_stats.accepted_tokens}/{benchmark_stats.generated_tokens})"
            )

            if benchmark_stats.acceptance_rate < acceptance_target and trial < args.trials:
                current_plan = tune_plan(current_plan, benchmark_stats.acceptance_rate)
                print(
                    "Acceptance below target; retuning and restarting llama-server with "
                    f"draft_min={current_plan.draft_min}, draft_max={current_plan.draft_max}, "
                    f"temperature={current_plan.temperature:.2f}, top_p={current_plan.top_p:.2f}"
                )
                continue

            print(
                f"Generating final output with n_predict={args.max_new_tokens} "
                f"and the same speculative settings."
            )
            final_start = len(server.snapshot_logs())
            final_response = server.completion(
                prompt=prompt,
                n_predict=args.max_new_tokens,
                temperature=current_plan.temperature,
                top_p=current_plan.top_p,
                cache_prompt=True,
            )
            final_stats = server.wait_for_stats(
                start_index=final_start,
                timeout=min(float(args.request_timeout), 120.0),
            )

            content = final_response.get("content")
            if content is None:
                raise RuntimeError(
                    "llama-server completion response did not include a 'content' field."
                )

            if final_stats is not None:
                print(
                    "\n=== Runtime Summary ==="
                )
                print(
                    "Speculative acceptance: "
                    f"{final_stats.acceptance_rate * 100.0:.1f}% "
                    f"({final_stats.accepted_tokens}/{final_stats.generated_tokens})"
                )
            else:
                print("\n=== Runtime Summary ===")
                print("Speculative acceptance: unavailable")

            print(f"Endpoint: {base_url}/completion")
            print("\n=== Output ===")
            print(content.strip())
            return 0

    raise RuntimeError("Unexpected control flow in speculative runner.")


if __name__ == "__main__":
    raise SystemExit(run())
