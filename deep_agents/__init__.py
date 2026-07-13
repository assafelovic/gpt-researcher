"""Deep Agents x GPT Researcher example.

Runs GPT Researcher as the research engine inside a LangChain Deep Agent
harness: the main agent plans with todos, delegates sections to researcher
subagents with isolated context, offloads drafts to a filesystem, and
assembles a final cited report.
"""
