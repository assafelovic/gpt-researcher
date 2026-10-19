import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "actions"
    / "report_generation.py"
)


def _load_module():
    pkg = types.ModuleType("gpt_researcher")
    pkg.__path__ = [str(_PATH.parent.parent)]
    sys.modules.setdefault("gpt_researcher", pkg)
    actions = types.ModuleType("gpt_researcher.actions")
    actions.__path__ = [str(_PATH.parent)]
    sys.modules.setdefault("gpt_researcher.actions", actions)

    for name in [
        "gpt_researcher.config",
        "gpt_researcher.config.config",
        "gpt_researcher.utils",
        "gpt_researcher.utils.llm",
        "gpt_researcher.utils.logger",
        "gpt_researcher.prompts",
        "gpt_researcher.utils.enum",
    ]:
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    mock_logger = MagicMock()
    sys.modules["gpt_researcher.utils.logger"].get_formatted_logger = lambda: (
        mock_logger
    )
    sys.modules["gpt_researcher.prompts"].PromptFamily = object
    sys.modules["gpt_researcher.prompts"].get_prompt_by_report_type = lambda *a, **k: (
        lambda *args, **kwargs: "PROMPT"
    )
    sys.modules["gpt_researcher.utils.enum"].Tone = SimpleNamespace
    sys.modules["gpt_researcher.config.config"].Config = object
    sys.modules["gpt_researcher.utils.llm"].create_chat_completion = AsyncMock(
        return_value="REPORT"
    )

    mod_name = "gpt_researcher.actions.report_generation_under_test_err"
    spec = importlib.util.spec_from_file_location(mod_name, _PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod, mock_logger


def _cfg():
    return SimpleNamespace(
        smart_llm_model="test-model",
        smart_llm_provider="test-provider",
        llm_kwargs={},
        report_format="markdown",
        total_words=100,
        language="en",
        stream_output=False,
        smart_token_limit=4000,
    )


def test_generate_report_raises_when_all_attempts_fail():
    mod, mock_logger = _load_module()

    async def _run():
        with patch.object(
            mod, "create_chat_completion", new_callable=AsyncMock
        ) as mock_cc:
            test_error = RuntimeError("LLM connection refused")
            mock_cc.side_effect = test_error

            with pytest.raises(RuntimeError, match="LLM connection refused"):
                await mod.generate_report(
                    query="What is solar power?",
                    context="Solar panels turn sunlight into electricity.",
                    agent_role_prompt="You are a research assistant.",
                    report_type="research_report",
                    tone="objective",
                    report_source="web",
                    websocket=None,
                    cfg=_cfg(),
                )

            assert mock_cc.call_count == 2
            mock_logger.error.assert_called_with(
                "Error in generate_report: LLM connection refused"
            )

    asyncio.run(_run())


def test_generate_report_succeeds_on_fallback():
    mod, mock_logger = _load_module()

    async def _run():
        with patch.object(
            mod, "create_chat_completion", new_callable=AsyncMock
        ) as mock_cc:
            # First attempt fails (e.g. system role rejection), second attempt succeeds
            mock_cc.side_effect = [
                ValueError("System role not supported"),
                "Report from fallback",
            ]

            report = await mod.generate_report(
                query="What is solar power?",
                context="Solar panels turn sunlight into electricity.",
                agent_role_prompt="You are a research assistant.",
                report_type="research_report",
                tone="objective",
                report_source="web",
                websocket=None,
                cfg=_cfg(),
            )

            assert report == "Report from fallback"
            assert mock_cc.call_count == 2
            mock_logger.error.assert_not_called()

    asyncio.run(_run())


def test_generate_report_succeeds_on_first_attempt():
    mod, mock_logger = _load_module()

    async def _run():
        with patch.object(
            mod, "create_chat_completion", new_callable=AsyncMock
        ) as mock_cc:
            mock_cc.return_value = "Report from first attempt"

            report = await mod.generate_report(
                query="What is solar power?",
                context="Solar panels turn sunlight into electricity.",
                agent_role_prompt="You are a research assistant.",
                report_type="research_report",
                tone="objective",
                report_source="web",
                websocket=None,
                cfg=_cfg(),
            )

            assert report == "Report from first attempt"
            assert mock_cc.call_count == 1
            mock_logger.error.assert_not_called()

    asyncio.run(_run())
