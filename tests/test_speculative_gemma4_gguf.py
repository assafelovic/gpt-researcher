from __future__ import annotations

from types import SimpleNamespace

from scripts.speculative_gemma4_gguf import (
    ModelSource,
    SpeculativePlan,
    build_server_command,
    discover_local_draft_model,
    extract_acceptance_stats,
)


def base_args() -> SimpleNamespace:
    return SimpleNamespace(
        server_path="/bin/llama-server",
        host="127.0.0.1",
        port=8091,
        context_length=4096,
        threads=8,
        parallel=1,
        n_gpu_layers=999,
        ctk="f32",
        ctv="f32",
        flash_attn="off",
        alias="gemma4-obliterated-gguf",
    )


def test_discover_local_draft_model_prefers_local_candidate(tmp_path):
    target = tmp_path / "gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf"
    target.write_bytes(b"x" * 10)
    (tmp_path / "gemma-4-E4B-it-OBLITERATED-Q4_K_M.1.gguf").write_bytes(b"x" * 12)
    (tmp_path / "ggml-vocab-gemma-4.gguf").write_bytes(b"x" * 2)
    draft = tmp_path / "gemma4-e4b-q4_k_m.gguf"
    draft.write_bytes(b"x" * 8)

    chosen = discover_local_draft_model(target, [tmp_path], strict_smaller=False)

    assert chosen == draft


def test_discover_local_draft_model_respects_strict_smaller(tmp_path):
    target = tmp_path / "target.gguf"
    target.write_bytes(b"x" * 10)
    draft = tmp_path / "draft.gguf"
    draft.write_bytes(b"x" * 20)

    chosen = discover_local_draft_model(target, [tmp_path], strict_smaller=True)

    assert chosen is None


def test_build_server_command_uses_local_draft_flags(tmp_path):
    target = tmp_path / "target.gguf"
    target.write_bytes(b"x")
    draft = tmp_path / "draft.gguf"
    draft.write_bytes(b"y")
    plan = SpeculativePlan(
        temperature=0.0,
        top_p=1.0,
        draft_min=0,
        draft_max=8,
        spec_type=None,
        spec_ngram_size_n=24,
        spec_ngram_size_m=48,
        spec_ngram_min_hits=1,
    )

    cmd = build_server_command(
        server_path="/bin/llama-server",
        target_source=ModelSource("local", str(target)),
        draft_source=ModelSource("local", str(draft)),
        plan=plan,
        host="127.0.0.1",
        port=8091,
        context_length=4096,
        threads=8,
        parallel=1,
        gpu_layers=999,
        ctk="f32",
        ctv="f32",
        flash_attn="off",
        alias="gemma4-obliterated-gguf",
    )

    assert "-m" in cmd and str(target) in cmd
    assert "-md" in cmd and str(draft) in cmd
    assert "--spec-type" not in cmd


def test_build_server_command_uses_ngram_flags_without_draft():
    plan = SpeculativePlan(
        temperature=0.0,
        top_p=1.0,
        draft_min=0,
        draft_max=8,
        spec_type="ngram-mod",
        spec_ngram_size_n=24,
        spec_ngram_size_m=48,
        spec_ngram_min_hits=1,
    )

    cmd = build_server_command(
        server_path="/bin/llama-server",
        target_source=ModelSource("hf", "llmware/gemma-4-2b-it-gguf:Q4_K_M"),
        draft_source=None,
        plan=plan,
        host="127.0.0.1",
        port=8091,
        context_length=4096,
        threads=8,
        parallel=1,
        gpu_layers=999,
        ctk="f32",
        ctv="f32",
        flash_attn="off",
        alias="gemma4-obliterated-gguf",
    )

    assert "-hf" in cmd
    assert "--spec-type" in cmd and "ngram-mod" in cmd
    assert "--spec-ngram-size-n" in cmd
    assert "--spec-ngram-size-m" in cmd


def test_extract_acceptance_stats_acceptance_line():
    stats = extract_acceptance_stats(
        [
            "llama.cpp log line",
            "draft acceptance rate = 0.70312 (   90 accepted /   128 generated)",
        ]
    )

    assert stats is not None
    assert stats.acceptance_rate == 0.70312
    assert stats.accepted_tokens == 90
    assert stats.generated_tokens == 128


def test_extract_acceptance_stats_ngram_stats_line():
    stats = extract_acceptance_stats(
        [
            "statistics ngram_mod: #calls = 810, #gen drafts = 15, #acc drafts = 15, "
            "#gen tokens = 960, #acc tokens = 730, dur(b,g,a) = 0.149, 0.347, 0.005 ms"
        ]
    )

    assert stats is not None
    assert round(stats.acceptance_rate, 6) == round(730 / 960, 6)
    assert stats.accepted_tokens == 730
    assert stats.generated_tokens == 960
