#!/usr/bin/env python3
"""
Speculative decoding runner for Gemma 4 obliterated checkpoints.

Important:
- This script expects a Hugging Face checkpoint or a local safetensors
  directory. GGUF files served by llama.cpp cannot be loaded by transformers.
- The target model is loaded in 4-bit with bitsandbytes.
- Flash Attention 2 is enabled when available, with SDPA fallback.
- Raw prompting is used. No chat template is applied.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_PACKAGES = ("transformers", "accelerate", "bitsandbytes", "sentencepiece")
DEFAULT_TARGET_MODEL = os.environ.get(
    "TARGET_MODEL", "Deepdive404/gemma-4-E4B-it-OBLITERATED"
)
DEFAULT_ASSISTANT_MODEL = os.environ.get(
    "ASSISTANT_MODEL", "wangzhang/gemma-4-E2B-it-abliterated"
)
DEFAULT_MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "256"))
DEFAULT_BENCHMARK_TOKENS = int(os.environ.get("BENCHMARK_TOKENS", "64"))


@dataclass
class SpeculativeSettings:
    do_sample: bool
    target_temperature: float
    target_top_p: float
    draft_temperature: float
    draft_top_p: float
    num_assistant_tokens: int
    num_assistant_tokens_schedule: str
    assistant_confidence_threshold: float


def bootstrap_dependencies(packages: Iterable[str]) -> None:
    """Install any missing runtime dependencies with pip."""

    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
    if not missing:
        return

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *missing]
    print(f"Installing missing packages: {', '.join(missing)}")
    subprocess.check_call(cmd)


def load_runtime_modules():
    """Import runtime modules after optional bootstrapping."""

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    return torch, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def is_gguf_reference(ref: str) -> bool:
    return ref.strip().lower().endswith(".gguf")


def normalize_checkpoint_reference(ref: str) -> str:
    """Resolve a local checkpoint reference or return the Hub id unchanged."""

    candidate = ref.strip()
    if not candidate:
        raise ValueError("Empty model reference.")

    path = Path(candidate).expanduser()
    if path.exists():
        if path.is_file() and is_gguf_reference(candidate):
            raise ValueError(
                f"{candidate} is a GGUF file. transformers speculative decoding needs "
                "a Hugging Face safetensors checkpoint or a local model directory."
            )
        if path.is_file():
            raise ValueError(
                f"{candidate} points to a file. Pass a Hugging Face checkpoint "
                "directory instead."
            )
        if not (path / "config.json").exists():
            raise ValueError(
                f"{candidate} does not look like a transformers checkpoint directory."
            )
        return str(path)

    if is_gguf_reference(candidate):
        raise ValueError(
            f"{candidate} is a GGUF file. Use a Hugging Face checkpoint for "
            "transformers-based speculative decoding."
        )

    return candidate


def choose_attention_implementation(torch_module) -> str:
    """Pick the fastest attention backend that is likely available."""

    if not torch_module.cuda.is_available():
        return "sdpa"

    try:
        import flash_attn  # noqa: F401

        return "flash_attention_2"
    except Exception:
        return "sdpa"


def load_tokenizer(tokenizer_ref: str, auto_tokenizer, *, trust_remote_code: bool = False):
    tokenizer = auto_tokenizer.from_pretrained(
        tokenizer_ref,
        use_fast=True,
        trust_remote_code=trust_remote_code,
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token
    return tokenizer


def load_quantized_model(
    model_ref: str,
    *,
    torch_module,
    auto_model,
    bitsandbytes_config_cls,
    load_in_4bit: bool,
    attention_implementation: str,
    compute_dtype,
):
    model_kwargs = {
        "device_map": "auto",
        "low_cpu_mem_usage": True,
        "trust_remote_code": False,
        "attn_implementation": attention_implementation,
    }

    if load_in_4bit:
        model_kwargs["quantization_config"] = bitsandbytes_config_cls(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=compute_dtype,
        )
    else:
        model_kwargs["torch_dtype"] = compute_dtype

    try:
        model = auto_model.from_pretrained(model_ref, **model_kwargs)
    except Exception as exc:
        if attention_implementation == "flash_attention_2":
            print(f"Flash Attention 2 load failed for {model_ref}: {exc}")
            print("Retrying with SDPA.")
            model_kwargs["attn_implementation"] = "sdpa"
            model = auto_model.from_pretrained(model_ref, **model_kwargs)
        else:
            raise

    model.eval()
    return model


def model_device(model, torch_module):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch_module.device("cpu")


def build_raw_prompt(user_prompt: str, system_prompt: str | None = None) -> str:
    parts: list[str] = []
    if system_prompt:
        parts.append("System instruction:\n" + system_prompt.strip())
    parts.append("User request:\n" + user_prompt.strip())
    parts.append("Assistant:")
    return "\n\n".join(parts)


def is_ablated_or_unfiltered(model_ref: str) -> bool:
    lowered = model_ref.lower()
    markers = ("abliterated", "uncensored", "unfiltered", "obliterated", "heretic", "decensored")
    return any(marker in lowered for marker in markers)


def derive_speculative_settings(assistant_ref: str, *, do_sample: bool) -> SpeculativeSettings:
    if is_ablated_or_unfiltered(assistant_ref):
        return SpeculativeSettings(
            do_sample=do_sample,
            target_temperature=0.0,
            target_top_p=1.0,
            draft_temperature=0.0 if not do_sample else 0.2,
            draft_top_p=1.0 if not do_sample else 0.95,
            num_assistant_tokens=12,
            num_assistant_tokens_schedule="heuristic_transient",
            assistant_confidence_threshold=0.40,
        )

    return SpeculativeSettings(
        do_sample=do_sample,
        target_temperature=0.0,
        target_top_p=1.0,
        draft_temperature=0.0 if not do_sample else 0.10,
        draft_top_p=1.0 if not do_sample else 0.85,
        num_assistant_tokens=6,
        num_assistant_tokens_schedule="heuristic_transient",
        assistant_confidence_threshold=0.58,
    )


def tune_settings_for_acceptance(settings: SpeculativeSettings, acceptance_rate: float) -> SpeculativeSettings:
    """Push the assistant toward a safer, higher-acceptance regime."""

    if acceptance_rate >= 0.70:
        return settings

    num_assistant_tokens = max(4, settings.num_assistant_tokens - 2)
    assistant_confidence_threshold = min(0.95, settings.assistant_confidence_threshold + 0.05)

    draft_temperature = settings.draft_temperature
    draft_top_p = settings.draft_top_p
    if settings.do_sample:
        draft_temperature = max(0.0, draft_temperature - 0.05)
        draft_top_p = max(0.75, draft_top_p - 0.05)

    return SpeculativeSettings(
        do_sample=settings.do_sample,
        target_temperature=settings.target_temperature,
        target_top_p=settings.target_top_p,
        draft_temperature=draft_temperature,
        draft_top_p=draft_top_p,
        num_assistant_tokens=num_assistant_tokens,
        num_assistant_tokens_schedule=settings.num_assistant_tokens_schedule,
        assistant_confidence_threshold=assistant_confidence_threshold,
    )


def set_assistant_generation_overrides(model, settings: SpeculativeSettings) -> None:
    """Persist speculative settings on the assistant model's generation config."""

    gc = model.generation_config
    gc.do_sample = settings.do_sample
    gc.temperature = settings.draft_temperature
    gc.top_p = settings.draft_top_p
    gc.num_assistant_tokens = settings.num_assistant_tokens
    gc.num_assistant_tokens_schedule = settings.num_assistant_tokens_schedule
    gc.assistant_confidence_threshold = settings.assistant_confidence_threshold


def speculative_acceptance_benchmark(
    target_model,
    assistant_model,
    tokenizer,
    prompt_ids,
    settings: SpeculativeSettings,
    max_new_tokens: int,
    torch_module,
):
    """Run a greedy speculative benchmark and return acceptance statistics."""

    total_proposed = 0
    total_accepted = 0
    produced = 0
    current = prompt_ids.to(model_device(target_model, torch_module))
    device = model_device(target_model, torch_module)

    assistant_kwargs = {
        "do_sample": settings.do_sample,
        "temperature": settings.draft_temperature,
        "top_p": settings.draft_top_p,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "return_dict_in_generate": True,
        "cache_implementation": "static",
    }

    with torch_module.inference_mode():
        while produced < max_new_tokens:
            remaining = max_new_tokens - produced
            draft_len = min(settings.num_assistant_tokens, remaining)
            if draft_len <= 0:
                break

            draft_kwargs = dict(assistant_kwargs)
            draft_kwargs["max_new_tokens"] = draft_len
            draft_kwargs["input_ids"] = current
            draft_kwargs["attention_mask"] = torch_module.ones_like(current)

            try:
                draft_output = assistant_model.generate(**draft_kwargs)
            except Exception:
                draft_kwargs.pop("cache_implementation", None)
                draft_output = assistant_model.generate(**draft_kwargs)

            draft_tokens = draft_output.sequences[:, current.shape[1] :]
            if draft_tokens.numel() == 0:
                break

            total_proposed += draft_tokens.shape[1]
            full_ids = torch_module.cat([current, draft_tokens], dim=1).to(device)
            logits = target_model(full_ids).logits

            matched = 0
            prompt_len = current.shape[1]
            for idx, token_id in enumerate(draft_tokens[0].tolist()):
                target_token = int(torch_module.argmax(logits[0, prompt_len + idx - 1]).item())
                if target_token == token_id:
                    matched += 1
                else:
                    break

            total_accepted += matched
            produced += matched

            if matched < draft_tokens.shape[1]:
                next_token = int(torch_module.argmax(logits[0, prompt_len + matched - 1]).item())
                append_token = torch_module.tensor([[next_token]], device=device, dtype=current.dtype)
                current = torch_module.cat([current[:, : prompt_len + matched], append_token], dim=1)
                produced += 1
                if tokenizer.eos_token_id is not None and next_token == tokenizer.eos_token_id:
                    break
            else:
                current = full_ids
                if (
                    tokenizer.eos_token_id is not None
                    and draft_tokens[0, -1].item() == tokenizer.eos_token_id
                ):
                    break

    acceptance_rate = total_accepted / total_proposed if total_proposed else 0.0
    return {
        "acceptance_rate": acceptance_rate,
        "accepted_tokens": total_accepted,
        "proposed_tokens": total_proposed,
        "generated_tokens": produced,
    }


def run_speculative_generation(
    target_model,
    assistant_model,
    tokenizer,
    assistant_tokenizer,
    prompt_ids,
    settings: SpeculativeSettings,
    max_new_tokens: int,
    torch_module,
    *,
    use_uad: bool,
):
    """Generate text with target_model.generate(..., assistant_model=...)."""

    device = model_device(target_model, torch_module)
    generation_kwargs = {
        "input_ids": prompt_ids.to(device),
        "attention_mask": torch_module.ones_like(prompt_ids).to(device),
        "assistant_model": assistant_model,
        "do_sample": settings.do_sample,
        "temperature": settings.target_temperature,
        "top_p": settings.target_top_p,
        "max_new_tokens": max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "num_assistant_tokens": settings.num_assistant_tokens,
        "num_assistant_tokens_schedule": settings.num_assistant_tokens_schedule,
        "assistant_confidence_threshold": settings.assistant_confidence_threshold,
        "cache_implementation": "static",
    }

    if use_uad:
        generation_kwargs["tokenizer"] = tokenizer
        generation_kwargs["assistant_tokenizer"] = assistant_tokenizer

    try:
        return target_model.generate(**generation_kwargs)
    except Exception:
        generation_kwargs.pop("cache_implementation", None)
        return target_model.generate(**generation_kwargs)


def load_model_pair(
    torch_module,
    auto_model,
    auto_tokenizer,
    bitsandbytes_config_cls,
    target_ref: str,
    assistant_ref: str,
):
    attention_impl = choose_attention_implementation(torch_module)
    compute_dtype = (
        torch_module.bfloat16
        if torch_module.cuda.is_available() and torch_module.cuda.is_bf16_supported()
        else torch_module.float16
    )

    target_tokenizer = load_tokenizer(target_ref, auto_tokenizer)
    assistant_tokenizer = load_tokenizer(assistant_ref, auto_tokenizer)

    target_model = load_quantized_model(
        target_ref,
        torch_module=torch_module,
        auto_model=auto_model,
        bitsandbytes_config_cls=bitsandbytes_config_cls,
        load_in_4bit=True,
        attention_implementation=attention_impl,
        compute_dtype=compute_dtype,
    )

    assistant_model = load_quantized_model(
        assistant_ref,
        torch_module=torch_module,
        auto_model=auto_model,
        bitsandbytes_config_cls=bitsandbytes_config_cls,
        load_in_4bit=False,
        attention_implementation=attention_impl,
        compute_dtype=compute_dtype,
    )

    return target_model, assistant_model, target_tokenizer, assistant_tokenizer, attention_impl


def pick_assistant_reference(explicit: str | None, target_ref: str) -> str:
    if explicit:
        return normalize_checkpoint_reference(explicit)

    candidates = [DEFAULT_ASSISTANT_MODEL, "google/gemma-4-E2B-it", "google/gemma-4-E2B"]

    seen: set[str] = set()
    ordered: list[str] = []
    for ref in candidates:
        ref = ref.strip()
        if ref and ref not in seen:
            seen.add(ref)
            ordered.append(ref)

    errors: list[str] = []
    for ref in ordered:
        try:
            return normalize_checkpoint_reference(ref)
        except Exception as exc:
            errors.append(f"{ref}: {exc}")

    raise RuntimeError(
        "Could not resolve any assistant model.\n" + "\n".join(errors)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gemma 4 speculative decoding runner with a 4-bit target model."
    )
    parser.add_argument(
        "--target-model",
        default=DEFAULT_TARGET_MODEL,
        help="Hugging Face id or local safetensors directory for the target model.",
    )
    parser.add_argument(
        "--assistant-model",
        default=None,
        help="Optional assistant model id or local safetensors directory.",
    )
    parser.add_argument(
        "--prompt",
        default="Explain speculative decoding and why assistant_model speeds up inference.",
        help="Raw user prompt. No chat template is used.",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Optional raw system instruction to prepend to the prompt.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=DEFAULT_MAX_NEW_TOKENS,
        help="Number of tokens to generate in the final run.",
    )
    parser.add_argument(
        "--benchmark-new-tokens",
        type=int,
        default=DEFAULT_BENCHMARK_TOKENS,
        help="Number of tokens to use for the acceptance benchmark.",
    )
    parser.add_argument(
        "--target-acceptance",
        type=float,
        default=0.70,
        help="Desired speculative token acceptance rate.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Enable sampling mode. Greedy mode is the default and is easier to benchmark exactly.",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Install missing Python dependencies before running.",
    )
    parser.add_argument(
        "--autotune-trials",
        type=int,
        default=3,
        help="How many tuning passes to use if acceptance starts below the target.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.bootstrap:
        bootstrap_dependencies(REQUIRED_PACKAGES)

    torch_module, auto_model, auto_tokenizer, bitsandbytes_config_cls = load_runtime_modules()

    if not torch_module.cuda.is_available():
        raise RuntimeError(
            "CUDA is required for 4-bit Gemma 4 speculative decoding with Flash Attention 2."
        )

    target_ref = normalize_checkpoint_reference(args.target_model)
    assistant_ref = pick_assistant_reference(args.assistant_model, target_ref)

    print(f"Target model:    {target_ref}")
    print(f"Assistant model: {assistant_ref}")

    target_model, assistant_model, tokenizer, assistant_tokenizer, attention_impl = load_model_pair(
        torch_module,
        auto_model,
        auto_tokenizer,
        bitsandbytes_config_cls,
        target_ref,
        assistant_ref,
    )

    same_tokenizer = (
        tokenizer.vocab_size == assistant_tokenizer.vocab_size
        and tokenizer.eos_token_id == assistant_tokenizer.eos_token_id
        and tokenizer.bos_token_id == assistant_tokenizer.bos_token_id
    )

    if not same_tokenizer:
        print(
            "Tokenizers do not look identical. The final generate() call will use UAD fallbacks, "
            "and the acceptance benchmark may be less exact."
        )

    settings = derive_speculative_settings(assistant_ref, do_sample=args.sample)

    prompt = build_raw_prompt(args.prompt, args.system)
    encoded = tokenizer(prompt, return_tensors="pt")
    prompt_ids = encoded["input_ids"]

    benchmark = None
    for trial in range(1, max(1, args.autotune_trials) + 1):
        benchmark = speculative_acceptance_benchmark(
            target_model=target_model,
            assistant_model=assistant_model,
            tokenizer=tokenizer,
            prompt_ids=prompt_ids,
            settings=settings,
            max_new_tokens=args.benchmark_new_tokens,
            torch_module=torch_module,
        )

        rate_pct = benchmark["acceptance_rate"] * 100.0
        print(
            f"Benchmark trial {trial}: accepted {benchmark['accepted_tokens']}/"
            f"{benchmark['proposed_tokens']} speculative tokens "
            f"({rate_pct:.1f}% acceptance)"
        )

        if benchmark["acceptance_rate"] >= args.target_acceptance:
            break

        settings = tune_settings_for_acceptance(settings, benchmark["acceptance_rate"])
        print(
            "Tuning speculative settings for better acceptance: "
            f"num_assistant_tokens={settings.num_assistant_tokens}, "
            f"assistant_confidence_threshold={settings.assistant_confidence_threshold:.2f}, "
            f"draft_temperature={settings.draft_temperature:.2f}, "
            f"draft_top_p={settings.draft_top_p:.2f}"
        )

    set_assistant_generation_overrides(assistant_model, settings)

    start = time.perf_counter()
    final_ids = run_speculative_generation(
        target_model=target_model,
        assistant_model=assistant_model,
        tokenizer=tokenizer,
        assistant_tokenizer=assistant_tokenizer,
        prompt_ids=prompt_ids,
        settings=settings,
        max_new_tokens=args.max_new_tokens,
        torch_module=torch_module,
        use_uad=not same_tokenizer,
    )
    elapsed = time.perf_counter() - start

    generated_ids = final_ids[0, prompt_ids.shape[1] :]
    text = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    ).strip()

    throughput = len(generated_ids) / elapsed if elapsed > 0 else 0.0
    benchmark_rate = benchmark["acceptance_rate"] * 100.0 if benchmark else 0.0

    print("\n=== Runtime Summary ===")
    print(f"Attention backend: {attention_impl}")
    print(f"Speculative acceptance: {benchmark_rate:.1f}%")
    print(f"Generated tokens: {len(generated_ids)}")
    print(f"Throughput: {throughput:.2f} tokens/s")
    print("\n=== Output ===")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
