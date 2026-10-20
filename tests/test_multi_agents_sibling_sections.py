"""#1495: sections are researched in parallel, so each writer is told what the
other sections cover. Runs the real editor LangGraph workflow, because a key
missing from DraftState is silently dropped between nodes."""

import asyncio

from multi_agents.agents import editor as editor_mod
from multi_agents.agents import researcher as researcher_mod


class FakeGPTResearcher:
    written = {}

    def __init__(self, query, **kwargs):
        self.query = query

    async def conduct_research(self):
        return []

    async def write_report(self, existing_headers=None, **kwargs):
        FakeGPTResearcher.written[self.query] = existing_headers
        return f"report on {self.query}"


def test_each_parallel_section_is_told_about_its_siblings(monkeypatch):
    monkeypatch.setattr(researcher_mod, "GPTResearcher", FakeGPTResearcher)
    FakeGPTResearcher.written = {}

    editor = editor_mod.EditorAgent()
    state = {
        "task": {"query": "Solid-state batteries", "follow_guidelines": False, "verbose": False},
        "title": "Solid-state batteries",
        "sections": ["Materials", "Manufacturing", "Market outlook"],
    }
    result = asyncio.run(editor.run_parallel_research(state))

    assert len(result["research_data"]) == 3
    for section in state["sections"]:
        siblings = [h["subtopic task"] for h in FakeGPTResearcher.written[section]]
        assert siblings == [s for s in state["sections"] if s != section]


def test_single_section_has_no_siblings():
    editor = editor_mod.EditorAgent()
    task_input = editor._create_task_input({"task": {}}, "Only", "T", ["Only"])
    assert task_input["sibling_sections"] == []
