from __future__ import annotations

from multi_agents.agents.editor import EditorAgent
from multi_agents.agents.human import HumanAgent

# Below import should remain last since it imports all of the above
from multi_agents.agents.orchestrator import ChiefEditorAgent
from multi_agents.agents.publisher import PublisherAgent
from multi_agents.agents.researcher import ResearchAgent
from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent
from multi_agents.agents.writer import WriterAgent

__all__ = [
    "ChiefEditorAgent",
    "ResearchAgent",
    "WriterAgent",
    "EditorAgent",
    "PublisherAgent",
    "ReviserAgent",
    "ReviewerAgent",
    "HumanAgent",
]
