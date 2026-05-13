from gpt_researcher.utils.local_llm import resolve_ollama_base_url
from gpt_researcher.utils.ollama_setup import build_gemma4_obliterated_modelfile


def test_resolve_ollama_base_url_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    assert resolve_ollama_base_url() == "http://127.0.0.1:11434"


def test_resolve_ollama_base_url_normalizes_plain_host(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "127.0.0.1:11435/")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    assert resolve_ollama_base_url() == "http://127.0.0.1:11435"


def test_build_gemma4_obliterated_modelfile_is_minimal(tmp_path):
    gguf = tmp_path / "gemma-4-E4B-it-OBLITERATED-Q4_K_M.gguf"
    modelfile = build_gemma4_obliterated_modelfile(gguf)

    assert f"FROM {gguf.resolve()}" in modelfile
    assert "TEMPLATE" not in modelfile
    assert "SYSTEM" not in modelfile
    assert "PARAMETER num_ctx 2048" in modelfile
    assert "PARAMETER num_predict 1024" in modelfile
