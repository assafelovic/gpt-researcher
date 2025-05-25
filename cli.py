"""Provides a command line interface for the GPTResearcher class.

Usage:

```shell
python cli.py "<query>" --report_type <report_type>
```

"""
from __future__ import annotations

import argparse
import asyncio
import os

from argparse import RawTextHelpFormatter
from uuid import uuid4

from backend.report_type import DetailedReport
from dotenv import load_dotenv
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone

# =============================================================================
# CLI
# =============================================================================

cli = argparse.ArgumentParser(
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
    help="The query to conduct research on.",
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

# First, let's see what values are actually in the Tone enum
print([t.value for t in Tone])

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

# =============================================================================
# Main
# =============================================================================


async def main(args: argparse.Namespace):
    """Conduct research on the given query, generate the report, and write
    it as a markdown file to the output directory."""
    if args.report_type == "detailed_report":
        detailed_report = DetailedReport(
            query=args.query,
            query_domains=None,
            report_type="research_report",
            report_source="web_search",
        )

        report = await detailed_report.run()
    else:
        researcher = GPTResearcher(
            query=args.query,
            report_type=args.report_type,
            tone=Tone(args.tone.capitalize()),
        )

        await researcher.conduct_research()

        report: str = await researcher.write_report()

    # Write the report to a file
    artifact_filepath: str = f"outputs/task_{uuid4().hex[:10]}_{args.query.replace(' ', '_')}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(artifact_filepath, "w") as f:
        f.write(report)

    print(f"Report written to '{artifact_filepath}'")


if __name__ == "__main__":
    load_dotenv()
    args: argparse.Namespace = cli.parse_args()
    asyncio.run(main(args))
