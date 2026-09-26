import os
import runpy
import sys
import types
from pathlib import Path


def test_multi_agents_loads_env_before_tracing_checks(monkeypatch):
    calls = []

    dotenv_module = types.ModuleType("dotenv")

    def fake_load_dotenv():
        os.environ["MONOCLE_TRACING"] = "true"
        os.environ["MONOCLE_EXPORTERS"] = "console"
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        return True

    dotenv_module.load_dotenv = fake_load_dotenv
    monkeypatch.setitem(sys.modules, "dotenv", dotenv_module)

    monocle_module = types.ModuleType("monocle_apptrace")

    def fake_setup_monocle_telemetry(**kwargs):
        calls.append(kwargs)

    monocle_module.setup_monocle_telemetry = fake_setup_monocle_telemetry
    monkeypatch.setitem(sys.modules, "monocle_apptrace", monocle_module)

    agents_module = types.ModuleType("multi_agents.agents")
    agents_module.ChiefEditorAgent = object
    monkeypatch.setitem(sys.modules, "multi_agents.agents", agents_module)

    enum_module = types.ModuleType("gpt_researcher.utils.enum")

    class Tone:
        Objective = "objective"

    enum_module.Tone = Tone
    monkeypatch.setitem(sys.modules, "gpt_researcher.utils.enum", enum_module)

    for name in (
        "MONOCLE_TRACING",
        "MONOCLE_EXPORTERS",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_TRACING_V2",
    ):
        monkeypatch.delenv(name, raising=False)

    script = Path(__file__).resolve().parents[1] / "multi_agents" / "main.py"
    runpy.run_path(str(script), run_name="_gptr_multi_agents_env_order_test")

    assert calls == [
        {
            "workflow_name": "gpt-researcher",
            "monocle_exporters_list": "console",
        }
    ]
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
