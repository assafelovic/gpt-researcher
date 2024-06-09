from agents import ChiefEditorAgent

chief_editor = ChiefEditorAgent({
  "query": "Is AI in a hype cycle?",
  "max_sections": 3,
  "follow_guidelines": False,
  "model": "gpt-4o",
  "guidelines": [
    "The report MUST be written in APA format",
    "Each sub section MUST include supporting sources using hyperlinks. If none exist, erase the sub section or rewrite it to be a part of the previous section",
    "The report MUST be written in spanish"
  ],
  "verbose": False
})
graph = chief_editor.init_research_team()
graph = graph.compile()
