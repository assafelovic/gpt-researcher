"""
Provides a command line interface for the GPTResearcher class.

Usage:

```shell
python cli.py "<query>" --report_type <report_type> --tone <tone> --query_domains <foo.com,bar.com>
```

"""

from __future__ import annotations

import asyncio

from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from backend.report_type import DetailedReport
from dotenv import load_dotenv
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from argparse import Namespace

logger: logging.Logger = get_formatted_logger("gpt_researcher")

# =============================================================================
# CLI
# =============================================================================

cli = ArgumentParser(
    description="Generate a research report.",
    # Enables the use of newlines in the help message
    formatter_class=RawTextHelpFormatter,
)

# =====================================
# Arg: Query
# =====================================

cli.add_argument(
    # Position 0 argument
    "query",
    type=str,
    help="The query to conduct research on.")

# =====================================
# Arg: Report Type
# =====================================

choices = [report_type.value for report_type in ReportType]

report_type_descriptions = {
    ReportType.ResearchReport.value: "Summary - Short and fast (~2 min)",
    ReportType.DetailedReport.value: "Detailed - In depth and longer (~5 min)",
    ReportType.ResourceReport.value: "",
    ReportType.OutlineReport.value: "",
    ReportType.CustomReport.value: "",
    ReportType.SubtopicReport.value: "",
    ReportType.DeepResearch.value: "Deep Research"
}

cli.add_argument(
    "--report_type",
    type=str,
    help="The type of report to generate. Options:\n" + "\n".join(
        f"  {choice}: {report_type_descriptions[choice]}" for choice in choices
    ),
    # Deserialize ReportType as a List of strings:
    choices=choices,
    required=True)

# =====================================
# Arg: Tone
# =====================================

cli.add_argument(
    "--tone",
    type=str,
    help="The tone of the report (optional).",
    choices=[
        "objective",
        "formal",
        "analytical",
        "persuasive",
        "informative",
        "explanatory",
        "descriptive",
        "critical",
        "comparative",
        "speculative",
        "reflective",
        "narrative",
        "humorous",
        "optimistic",
        "pessimistic",
    ],
    default="objective",
)

# =====================================
# Arg: Report Type
# =====================================

choices: list[str] = [report_type.value for report_type in ReportType]

report_type_descriptions: dict[str, str] = {
    ReportType.ResearchReport.value: "Summary - Short and fast (~2 min)",
    ReportType.DetailedReport.value: "Detailed - In depth and longer (~5 min)",
    ReportType.ResourceReport.value: "Resource - List of resources",
    ReportType.OutlineReport.value: "Outline - Skeleton of the report",
    ReportType.CustomReport.value: "Custom - Your Unique Report",
    ReportType.SubtopicReport.value: "Subtopic - Subtopic report",
}

cli.add_argument(
    "--report_type",
    type=str,
    help="The type of report to generate. Options:\n" + "\n".join(f"  {choice}: {report_type_descriptions[choice]}" for choice in choices),
    # Deserialize ReportType as a List of strings:
    choices=choices,
    required=True,
)

# =====================================
# Arg: Report Type
# =====================================

choices: list[str] = [report_type.value for report_type in ReportType]

report_type_descriptions: dict[str, str] = {
    ReportType.ResearchReport.value: "Summary - Short and fast (~2 min)",
    ReportType.DetailedReport.value: "Detailed - In depth and longer (~5 min)",
    ReportType.ResourceReport.value: "",
    ReportType.OutlineReport.value: "",
    ReportType.CustomReport.value: "",
    ReportType.SubtopicReport.value: "",
}

cli.add_argument(
    "--report_type",
    type=str,
    help="The type of report to generate. Options:\n" + "\n".join(f"  {choice}: {report_type_descriptions[choice]}" for choice in choices),
    # Deserialize ReportType as a List of strings:
    choices=choices,
    required=True,
)

# =====================================
# Arg: Query Domains
# =====================================

cli.add_argument(
    "--query_domains",
    type=str,
    help="A comma-separated list of domains to search for the query.",
    default="",
)

# =============================================================================
# Main
# =============================================================================


async def main(args) -> None:
    """Conduct research on the given query, generate the report, and write it as a markdown file to the output directory."""
    query_domains: list[str] = [] if args.query_domains is None else args.query_domains.split(",")

    if str(args.report_type).casefold() == ReportType.DetailedReport.value:
        detailed_report: DetailedReport = DetailedReport(
            query=args.query,
            query_domains=query_domains,
            report_type=ReportType.DetailedReport,
            report_source="web_search",
        )

        report: str = await detailed_report.run()
    else:
        # Convert the simple keyword to the full Tone enum value
        tone_map: dict[str, Tone] = {
            "objective": Tone.Objective,
            "formal": Tone.Formal,
            "analytical": Tone.Analytical,
            "persuasive": Tone.Persuasive,
            "informative": Tone.Informative,
            "explanatory": Tone.Explanatory,
            "descriptive": Tone.Descriptive,
            "critical": Tone.Critical,
            "comparative": Tone.Comparative,
            "speculative": Tone.Speculative,
            "reflective": Tone.Reflective,
            "narrative": Tone.Narrative,
            "humorous": Tone.Humorous,
            "optimistic": Tone.Optimistic,
            "pessimistic": Tone.Pessimistic,
        }

        researcher = GPTResearcher(
            query=args.query,
            query_domains=query_domains,
            report_type=args.report_type,
            tone=tone_map[str(args.tone).casefold()],
        )

        _research_result: str | list[str] = await researcher.conduct_research()
        # report: str = await researcher.write_report(_research_result if isinstance(_research_result, list) else [_research_result])

        report: str = await researcher.write_report()

    # Write the report to a file
    artifact_filepath: Path = Path("outputs", f"{uuid4().hex[:8]}.md")
    artifact_filepath.parent.mkdir(parents=True, exist_ok=True)
    artifact_filepath.write_text(report)

    msg = f"Report written to '{artifact_filepath}'"
    print(msg)
    logger.info(msg)


if __name__ == "__main__":
    load_dotenv()
    args: Namespace = cli.parse_args()
    asyncio.run(main(args))
