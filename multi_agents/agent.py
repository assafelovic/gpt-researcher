from __future__ import annotations

if __name__ == "__main__":
    import sys

    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))

from typing import TYPE_CHECKING

from multi_agents.agents import ChiefEditorAgent

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph, StateGraph

chief_editor = ChiefEditorAgent(
    {
        "query": "Is AI in a hype cycle?",
        "max_sections": 3,
        "follow_guidelines": False,
        "model": "gpt-4o",
        "guidelines": [
            "The report MUST be written in APA format",
            "Each sub section MUST include supporting sources using hyperlinks. If none exist, erase the sub section or rewrite it to be a part of the previous section",
            "The report MUST be written in spanish",
        ],
        "verbose": False,
    },
    websocket=None,
    stream_output=None,
)
graph: StateGraph = chief_editor.init_research_team()
compiled_graph: CompiledStateGraph = graph.compile()

compiled_graph.invoke({"query": "Is AI in a hype cycle?"})
