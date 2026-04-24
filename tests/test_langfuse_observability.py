import os

from gpt_researcher.utils import langfuse_observability


def clear_langfuse_env(monkeypatch):
    for key in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_BASE_URL",
        "LANGFUSE_HOST",
        "LANGFUSE_RECORD_IO",
        "AI_SDK_TELEMETRY_RECORD_IO",
    ):
        monkeypatch.delenv(key, raising=False)


def test_langfuse_status_defaults_to_disabled_without_credentials(monkeypatch):
    clear_langfuse_env(monkeypatch)

    status = langfuse_observability.get_langfuse_runtime_status()

    assert status["configured"] is False
    assert status["public_key"] is False
    assert status["secret_key"] is False
    assert status["base_url"] == "https://us.cloud.langfuse.com"
    assert status["record_io"] is False


def test_langfuse_status_uses_redacted_env(monkeypatch):
    clear_langfuse_env(monkeypatch)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    monkeypatch.setenv("AI_SDK_TELEMETRY_RECORD_IO", "true")

    status = langfuse_observability.get_langfuse_runtime_status()

    assert status["configured"] is True
    assert status["public_key"] is True
    assert status["secret_key"] is True
    assert status["base_url"] == "https://us.cloud.langfuse.com"
    assert status["record_io"] is True
    assert "pk-test" not in str(status)
    assert "sk-test" not in str(status)


def test_langfuse_observation_is_noop_without_credentials(monkeypatch):
    clear_langfuse_env(monkeypatch)

    with langfuse_observability.observe_langfuse(name="test") as observation:
        assert observation is None
        langfuse_observability.update_observation(
            observation,
            metadata={"status": "completed"},
        )

    assert "LANGFUSE_BASE_URL" not in os.environ
