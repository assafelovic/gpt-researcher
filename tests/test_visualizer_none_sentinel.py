import asyncio
import importlib.util
import sys
import types
from pathlib import Path


VISUALIZER_PATH = (
    Path(__file__).resolve().parents[1]
    / "multi_agents"
    / "agents"
    / "visualizer.py"
)


def _load_visualizer_module(monkeypatch):
    for package_name in (
        "multi_agents",
        "multi_agents.agents",
        "multi_agents.agents.utils",
    ):
        package = types.ModuleType(package_name)
        package.__path__ = []
        monkeypatch.setitem(sys.modules, package_name, package)

    sys.modules["multi_agents.agents.utils"].__path__ = [
        str(VISUALIZER_PATH.parent / "utils")
    ]

    views = types.ModuleType("multi_agents.agents.utils.views")
    views.print_agent_output = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, views.__name__, views)

    llms = types.ModuleType("multi_agents.agents.utils.llms")
    llms.call_model = None
    monkeypatch.setitem(sys.modules, llms.__name__, llms)

    spec = importlib.util.spec_from_file_location(
        "multi_agents.agents.visualizer",
        VISUALIZER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_visualizer_keeps_diagram_with_none_in_a_label(monkeypatch):
    visualizer_module = _load_visualizer_module(monkeypatch)
    diagram = '```mermaid\nflowchart LR\n    A["None reported"] --> B["Done"]\n```'

    async def return_diagram(*args, **kwargs):
        return diagram

    monkeypatch.setattr(visualizer_module, "call_model", return_diagram)

    result = asyncio.run(
        visualizer_module.VisualizerAgent().run(
            {"task": {"model": "gpt-4o"}, "research_data": []}
        )
    )

    assert result == {"diagrams": [diagram]}
