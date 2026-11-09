import pytest


@pytest.mark.asyncio
async def test_call_model_gives_reasoning_models_the_smart_token_budget(monkeypatch):
    from gpt_researcher.config.config import Config
    from multi_agents.agents.utils import llms

    seen = {}

    async def fake_completion(**kwargs):
        seen.update(kwargs)
        return '{"introduction": "Intro", "conclusion": "End"}'

    monkeypatch.setattr(llms, "create_chat_completion", fake_completion)
    result = await llms.call_model([{"role": "user", "content": "Write it"}], "gpt-5.4", response_format="json")

    cfg = Config()
    assert seen["max_tokens"] == cfg.smart_token_limit
    assert seen["reasoning_effort"] == cfg.reasoning_effort
    assert result == {"introduction": "Intro", "conclusion": "End"}


@pytest.mark.asyncio
async def test_writer_explains_an_empty_model_answer(monkeypatch):
    from multi_agents.agents import writer as writer_module

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(writer_module, "call_model", nothing)
    agent = writer_module.WriterAgent()
    state = {"title": "Heat", "research_data": [], "task": {"model": "gpt-5.4", "verbose": False}}
    with pytest.raises(RuntimeError, match="returned no introduction and conclusion"):
        await agent.run(state)
