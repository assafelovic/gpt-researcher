"""PublisherAgent.generate_layout guards for None sources/research_data."""
import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.modules.setdefault("multi_agents", types.ModuleType("multi_agents"))
sys.modules["multi_agents"].__path__ = [str(ROOT / "multi_agents")]
agents = types.ModuleType("multi_agents.agents")
agents.__path__ = [str(ROOT / "multi_agents" / "agents")]
sys.modules.setdefault("multi_agents.agents", agents)
utils = types.ModuleType("multi_agents.agents.utils")
utils.__path__ = [str(ROOT / "multi_agents" / "agents" / "utils")]
sys.modules.setdefault("multi_agents.agents.utils", utils)

ff = types.ModuleType("multi_agents.agents.utils.file_formats")
ff.write_md_to_pdf = ff.write_md_to_word = ff.write_text_to_md = None
sys.modules["multi_agents.agents.utils.file_formats"] = ff
views = types.ModuleType("multi_agents.agents.utils.views")
views.print_agent_output = lambda *a, **k: None
sys.modules["multi_agents.agents.utils.views"] = views

path = ROOT / "multi_agents/agents/publisher.py"
spec = importlib.util.spec_from_file_location("multi_agents.agents.publisher", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
PublisherAgent = mod.PublisherAgent


def test_none_sources_does_not_typeerror():
    agent = PublisherAgent(output_dir="/tmp")
    layout = agent.generate_layout(
        {
            "research_data": None,
            "sources": None,
            "headers": None,
            "diagrams": None,
            "introduction": "intro",
            "table_of_contents": "toc",
            "conclusion": "end",
            "date": "today",
        }
    )
    assert "intro" in layout
    assert isinstance(layout, str)
