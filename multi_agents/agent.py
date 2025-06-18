from __future__ import annotations

from langgraph.graph.state import CompiledStateGraph, StateGraph

from multi_agents.agents import ChiefEditorAgent

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
state_graph: StateGraph = chief_editor.init_research_team()
compiled_state_graph: CompiledStateGraph = state_graph.compile()

compiled_state_graph.invoke({"query": "Is AI in a hype cycle?"})
