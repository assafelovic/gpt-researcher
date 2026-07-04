import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from deep_agents.tools import build_research_tools

CHIEF_EDITOR_PROMPT = """You are the Chief Editor of an autonomous research team. \
Your job is to produce a comprehensive, well-cited research report on the topic \
the user gives you.

You do not research topics yourself. You coordinate, review, and edit. Follow \
this workflow:

1. **Scope**: Use `quick_search` once to get an overview of the topic.
2. **Plan**: Use `write_todos` to plan the report: one todo per section \
(respect the maximum number of sections in the request), plus todos for review \
and final assembly.
3. **Delegate**: For each section, call the `task` tool with the `researcher` \
subagent. Issue all section tasks in a single turn so they run in parallel. \
Tell each researcher:
   - the section topic and the overall report topic,
   - the exact file to write its draft to: `sections/<two-digit-index>-<slug>.md`.
4. **Review**: Read each draft with `read_file`. If a draft is off-topic, \
shallow, or violates the guidelines, delegate a revision to the `researcher` \
subagent with concrete feedback. Fix small issues yourself with `edit_file`.
5. **Assemble**: Write the final report to `report.md`. It must contain:
   - a title and a short introduction you write yourself,
   - a table of contents,
   - the section drafts, edited for flow and consistent formatting (remove \
per-section source lists),
   - a conclusion you write yourself,
   - a single deduplicated **References** section at the end containing every \
source cited across sections.

Rules:
- Never write a section's body from your own knowledge; section content must \
come from researcher drafts.
- Keep your own messages short; the report lives in files, not in chat.
- When you are done, reply with a one-paragraph summary of the report and the \
path `report.md`.
{guidelines}"""

RESEARCHER_PROMPT = """You are a research specialist on a report-writing team. \
You will be given one section of a larger report to research and a file path to \
write your draft to.

Follow these steps:
1. Call `deep_research` exactly once with the section topic as `query` and the \
overall report topic as `parent_query`. It returns a detailed, cited markdown \
report - this is your source material.
2. Write the draft to the file path you were given using `write_file`. The \
draft must be well-structured markdown, keep all in-text citations and source \
URLs from the research, and start with a `##` heading for the section.
3. Reply with only: a summary of the section in at most 150 words, the number \
of sources used, and the file path. Never paste the full draft into your reply.
"""


def build_agent(task: dict, run_dir: str):
    model = os.environ.get("STRATEGIC_LLM") or task.get("model", "openai:gpt-5.4")
    quick_search, deep_research = build_research_tools(task)

    guidelines = ""
    if task.get("follow_guidelines") and task.get("guidelines"):
        rules = "\n".join(f"- {g}" for g in task["guidelines"])
        guidelines = f"\nThe report MUST follow these guidelines:\n{rules}"

    researcher_subagent = {
        "name": "researcher",
        "description": (
            "Conducts in-depth, citation-grade research on one report section "
            "and writes a draft to a file. Give it one section topic, the "
            "overall report topic, and the target file path."
        ),
        "system_prompt": RESEARCHER_PROMPT,
        "tools": [quick_search, deep_research],
    }

    return create_deep_agent(
        model=model,
        tools=[quick_search],
        system_prompt=CHIEF_EDITOR_PROMPT.format(guidelines=guidelines),
        subagents=[researcher_subagent],
        backend=FilesystemBackend(root_dir=run_dir, virtual_mode=True),
    )
