"""PublisherAgent must publish a report when the task names no formats.

`multi_agents/agent.py` is the graph registered by both `langgraph.json` files
and its task dict has no `publish_formats` key, so the last node of the graph
used to raise `AttributeError: 'NoneType' object has no attribute 'get'` after
the whole team had already produced the report.
"""
import asyncio
import importlib.util
import pathlib
import sys
import types
from unittest.mock import patch

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_publisher():
    """Load publisher.py with its sibling utility modules stubbed out."""
    with patch.dict(sys.modules):
        for name, path in (
            ("multi_agents", ROOT / "multi_agents"),
            ("multi_agents.agents", ROOT / "multi_agents" / "agents"),
            ("multi_agents.agents.utils", ROOT / "multi_agents" / "agents" / "utils"),
        ):
            module = types.ModuleType(name)
            module.__path__ = [str(path)]
            sys.modules[name] = module

        file_formats = types.ModuleType("multi_agents.agents.utils.file_formats")
        file_formats.write_md_to_pdf = None
        file_formats.write_md_to_word = None
        file_formats.write_text_to_md = None
        sys.modules["multi_agents.agents.utils.file_formats"] = file_formats
        views = types.ModuleType("multi_agents.agents.utils.views")
        views.print_agent_output = lambda *a, **k: None
        sys.modules["multi_agents.agents.utils.views"] = views

        spec = importlib.util.spec_from_file_location(
            "multi_agents.agents.publisher", ROOT / "multi_agents/agents/publisher.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


publisher = _load_publisher()

# The task dict multi_agents/agent.py hands to ChiefEditorAgent: no publish_formats.
LANGGRAPH_TASK = {
    "query": "Is AI in a hype cycle?",
    "max_sections": 3,
    "max_plan_revisions": 3,
    "follow_guidelines": False,
    "model": "gpt-4o",
    "guidelines": ["The report MUST be written in APA format"],
    "verbose": False,
}


def research_state(task):
    return {
        "task": task,
        "title": "Is AI in a hype cycle?",
        "date": "today",
        "introduction": "Intro paragraph.",
        "table_of_contents": "- Section A",
        "research_data": {"Section A": "## Section A\n\nBody of section A."},
        "conclusion": "Conclusion paragraph.",
        "sources": ["- Source, 2026 [link](https://example.invalid/a)"],
        "diagrams": [],
        "headers": {"title": "T", "date": "Date", "introduction": "Introduction",
                    "table_of_contents": "Table of Contents", "conclusion": "Conclusion",
                    "references": "References"},
    }


def publish(output_dir, task):
    """Run the publisher with the three writers recorded instead of invoked."""
    written = []

    def recorder(kind):
        async def _write(layout, path):
            written.append((kind, layout))
            return f"{path}/{kind}"
        return _write

    agent = publisher.PublisherAgent(output_dir=str(output_dir))
    with patch.object(publisher, "write_md_to_pdf", recorder("pdf")), \
         patch.object(publisher, "write_md_to_word", recorder("docx")), \
         patch.object(publisher, "write_text_to_md", recorder("markdown")):
        state = asyncio.run(agent.run(research_state(task)))
    return state, written


@pytest.mark.parametrize("task", [LANGGRAPH_TASK, {**LANGGRAPH_TASK, "publish_formats": None}])
def test_missing_publish_formats_publishes_markdown(tmp_path, task):
    state, written = publish(tmp_path, task)

    assert [kind for kind, _ in written] == ["markdown"]
    layout = written[0][1]
    assert "Body of section A" in layout
    assert "Conclusion paragraph." in layout
    assert state["report"] == layout


def test_explicit_publish_formats_are_still_honoured(tmp_path):
    task = {**LANGGRAPH_TASK, "publish_formats": {"markdown": True, "pdf": True, "docx": False}}
    _state, written = publish(tmp_path, task)

    assert [kind for kind, _ in written] == ["pdf", "markdown"]
