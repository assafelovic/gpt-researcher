"""GPTResearcher(max_subtopics=...) must reach the subtopics prompt.

``construct_subtopics`` renders the outline prompt from ``cfg.max_subtopics``
(``MAX_SUBTOPICS``, default 3). The per-instance argument was stored on the
researcher and never applied, so the documented option (the pip-package guide
shows ``max_subtopics=5``) was silently ignored in favour of the config default.
"""

import gpt_researcher.utils.llm as llm_module
from gpt_researcher import GPTResearcher
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


class _RecordingModel:
    """Records the rendered prompt and answers with a valid subtopics payload."""

    def __init__(self, captured):
        self.captured = captured

    def __call__(self, prompt_value):
        text = (
            prompt_value.to_string()
            if hasattr(prompt_value, "to_string")
            else str(prompt_value)
        )
        self.captured["prompt"] = text
        return '{"subtopics": [{"task": "Battery chemistry"}]}'


def _install_fake_llm(monkeypatch, captured):
    class _Provider:
        def __init__(self):
            self.llm = _RecordingModel(captured)

    monkeypatch.setattr(llm_module, "get_llm", lambda provider, **kwargs: _Provider())


def _clear_config_env(monkeypatch):
    for key in list(DEFAULT_CONFIG) + ["CONFIG_PATH"]:
        monkeypatch.delenv(key, raising=False)


async def test_explicit_max_subtopics_reaches_the_prompt(monkeypatch):
    _clear_config_env(monkeypatch)
    captured = {}
    _install_fake_llm(monkeypatch, captured)

    researcher = GPTResearcher(query="battery chemistries", max_subtopics=7)
    await researcher.get_subtopics()

    assert "maximum of 7" in captured["prompt"]
    assert researcher.max_subtopics == 7


async def test_max_subtopics_falls_back_to_the_config_value(monkeypatch):
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("MAX_SUBTOPICS", "2")
    captured = {}
    _install_fake_llm(monkeypatch, captured)

    researcher = GPTResearcher(query="battery chemistries")
    await researcher.get_subtopics()

    assert "maximum of 2" in captured["prompt"]
    assert researcher.max_subtopics == 2
