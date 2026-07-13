import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gpt_researcher import GPTResearcher


def build_research_tools(task: dict, cost_tracker: dict | None = None):
    """Build the research tools with the task's source config bound in.

    The report source ("web", "local" or "hybrid") is task configuration, not
    something the agent should decide per call, so it is closed over here
    rather than exposed as a tool argument. For "local" and "hybrid", set the
    DOC_PATH env var to your documents directory.

    Pass a dict as cost_tracker to accumulate GPT Researcher API costs under
    its "total" key.
    """
    report_source = task.get("source", "web")

    def _track_cost(researcher: GPTResearcher):
        if cost_tracker is not None:
            cost_tracker["total"] = cost_tracker.get("total", 0.0) + researcher.get_costs()

    async def quick_search(query: str) -> str:
        """Run a fast web search and return the top results with snippets and URLs.

        Use this to scope a topic, verify a fact, or gather just enough context
        to plan a report outline. Results are raw snippets - iterate with
        refined queries if the first search does not surface what you need.
        For in-depth, citation-grade research on a section, use deep_research
        instead.
        """
        researcher = GPTResearcher(query=query, report_type="research_report", verbose=False)
        results = await researcher.quick_search(query)
        _track_cost(researcher)
        if isinstance(results, list):
            formatted = "\n\n".join(
                f"[{i}] {r.get('title') or ''}\n{r.get('body') or r.get('content') or ''}\n"
                f"URL: {r.get('href') or r.get('url') or ''}".strip()
                for i, r in enumerate(results, 1)
            )
            return formatted or "No results found."
        return results or "No results found."

    async def deep_research(query: str, parent_query: str = "") -> str:
        """Run the full GPT Researcher pipeline on a query.

        Plans sub-queries, gathers and validates dozens of sources (web pages
        and/or local documents, depending on the task configuration), and
        returns a detailed markdown research report with in-text citations and
        a reference list. This is slow (a few minutes) and thorough - use it
        once per report section, not for quick lookups.

        Args:
            query: The research question or section topic to investigate.
            parent_query: The overall report topic, when researching a section
                of a larger report. Keeps the research focused in context.
        """
        report_type = "subtopic_report" if parent_query else "research_report"
        researcher = GPTResearcher(
            query=query,
            report_type=report_type,
            report_source=report_source,
            parent_query=parent_query,
            verbose=False,
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        _track_cost(researcher)

        sources = researcher.get_source_urls()
        if sources:
            report += "\n\n### Sources\n\n" + "\n".join(f"- {url}" for url in sources)
        return report

    return quick_search, deep_research
