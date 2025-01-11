"""
Provides a command line interface for the GPTResearcher class.

Usage:

```shell
python cli.py "<query>" --report_type <report_type>
```

"""
import asyncio
import argparse
from argparse import RawTextHelpFormatter
from uuid import uuid4
import os

from dotenv import load_dotenv

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
from backend.report_type import DetailedReport

# =============================================================================
# CLI
# =============================================================================

cli = argparse.ArgumentParser(
    description="Generate a research report.",
    # Enables the use of newlines in the help message
    formatter_class=RawTextHelpFormatter)

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
    ReportType.SubtopicReport.value: ""
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

# First, let's see what values are actually in the Tone enum
print([t.value for t in Tone])

cli.add_argument(
    "--tone",
    type=str,
    help="The tone of the report (optional).",
    choices=["objective", "formal", "analytical", "persuasive", "informative", 
            "explanatory", "descriptive", "critical", "comparative", "speculative", 
            "reflective", "narrative", "humorous", "optimistic", "pessimistic"],
    default="objective"
)

# =============================================================================
# Main
# =============================================================================


async def main(args):
    """ 
    Conduct research on the given query, generate the report, and write
    it as a markdown file to the output directory.
    """
    if args.report_type == 'detailed_report':
        detailed_report = DetailedReport(
            query=args.query,
            report_type="research_report",
            report_source="web_search",
        )

        report = await detailed_report.run()
    else:
        # Convert the simple keyword to the full Tone enum value
        tone_map = {
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
            "pessimistic": Tone.Pessimistic
        }

        researcher = GPTResearcher(
            query=args.query,
            report_type=args.report_type,
            tone=tone_map[args.tone]
        )

        await researcher.conduct_research()

        report = await researcher.write_report()

    # Write the report to a file
    artifact_filepath = f"outputs/{uuid4()}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(artifact_filepath, "w") as f:
        f.write(report)

    print(f"Report written to '{artifact_filepath}'")

if __name__ == "__main__":
    load_dotenv()
    args = cli.parse_args()
    asyncio.run(main(args))
