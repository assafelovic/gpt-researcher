---
date: <% tp.file.creation_date() %>
modification_date: <% await tp.file.last_modified_date() %>
tags: 
  - gpt-researcher
prompt: {PROMPT}
---

Date:: [[<% tp.file.creation_date("YY-MM-DD-dddd") %>]]
ai-model:: [[gpt-researcher]]

{RESEARCH_REPORT}

# Agent Output

{AGENT_OUTPUT}