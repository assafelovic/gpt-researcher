"""
Provides a command line interface for the GPTResearcher class.

Usage:

```shell
python cli.py "<query>" --report_type <report_type>
```

"""

from __future__ import annotations

import asyncio
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from dotenv import load_dotenv

from backend.report_type import DetailedReporter
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.schemas import ReportType

if TYPE_CHECKING:
    from argparse import Namespace

logger = logging.getLogger()

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
    help="The query to conduct research on.",
)

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
}

cli.add_argument(
    "--report_type",
    type=str,
    help="The type of report to generate. Options:\n"
    + "\n".join(f"  {choice}: {report_type_descriptions[choice]}" for choice in choices),
    # Deserialize ReportType as a List of strings:
    choices=choices,
    required=True,
)

# =============================================================================
# Main
# =============================================================================


async def main(args: Namespace):
    """
    Conduct research on the given query and starts generating the report.

    Writes the report as a markdown file to the output directory.
    """
    if args.report_type == "detailed_report":
        detailed_report = DetailedReporter(
            query=args.query,
            report_type="research_report",
            report_source="web_search",
        )

        report = await detailed_report.run()
    else:
        researcher = GPTResearcher(
            query=args.query,
            report_type=args.report_type,
        )

        await researcher.conduct_research()

        report = await researcher.write_report()

    # Write the report to a file
    artifact_filepath = Path(
        "outputs", f"{uuid4().hex[:8]}.md"
    ).absolute()  # TODO: make this configurable.
    artifact_filepath.parent.mkdir(parents=True, exist_ok=True)
    artifact_filepath.write_text(report)

    logger.info(f"Report written to '{artifact_filepath}'")


if __name__ == "__main__":
    load_dotenv()
    args = cli.parse_args()
    asyncio.run(main(args))
