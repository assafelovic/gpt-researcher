"""
Provides a command line interface for the GPTResearcher class.

Usage:

```shell
python cli.py "<query>" --report_type <report_type> --tone <tone> --query_domains <foo.com,bar.com>
```

"""
import asyncio
import argparse
from argparse import RawTextHelpFormatter
from uuid import uuid4
import os

from dotenv import load_dotenv

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from backend.report_type import DetailedReport
from backend.utils import write_md_to_pdf, write_md_to_word

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
    choices=["objective", "formal", "analytical", "persuasive", "informative",
            "explanatory", "descriptive", "critical", "comparative", "speculative",
            "reflective", "narrative", "humorous", "optimistic", "pessimistic"],
    default="objective"
)

# =====================================
# Arg: Encoding
# =====================================

cli.add_argument(
    "--encoding",
    type=str,
    help="The encoding to use for the output file (default: utf-8).",
    default="utf-8"
)

# =====================================
# Arg: Query Domains
# =====================================

cli.add_argument(
    "--query_domains",
    type=str,
    help="A comma-separated list of domains to search for the query.",
    default=""
)

# =====================================
# Arg: Report Source
# =====================================

cli.add_argument(
    "--report_source",
    type=str,
    help="The source of information for the report.",
    choices=["web", "local", "hybrid", "azure", "langchain_documents",
             "langchain_vectorstore", "static"],
    default="web"
)

# =====================================
# Arg: Output Format Flags
# =====================================

cli.add_argument(
    "--no-pdf",
    action="store_true",
    help="Skip PDF generation (generate markdown and DOCX only)."
)

cli.add_argument(
    "--no-docx",
    action="store_true",
    help="Skip DOCX generation (generate markdown and PDF only)."
)

# =============================================================================
# Main
# =============================================================================

async def main(args):
    """
    Conduct research on the given query, generate the report, and write
    it as a markdown file to the output directory.
    """
    query_domains = args.query_domains.split(",") if args.query_domains else []

    if args.report_type == 'detailed_report':
        detailed_report = DetailedReport(
            query=args.query,
            query_domains=query_domains,
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
            query_domains=query_domains,
            report_type=args.report_type,
            report_source=args.report_source,
            tone=tone_map[args.tone],
            encoding=args.encoding
        )

        await researcher.conduct_research()

        report = await researcher.write_report()

    # Write the report to markdown file
    task_id = str(uuid4())
    artifact_filepath = f"outputs/{task_id}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(artifact_filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to '{artifact_filepath}'")

    # Generate PDF if not disabled
    if not args.no_pdf:
        try:
            pdf_path = await write_md_to_pdf(report, task_id)
            if pdf_path:
                print(f"PDF written to '{pdf_path}'")
        except Exception as e:
            print(f"Warning: PDF generation failed: {e}")

    # Generate DOCX if not disabled
    if not args.no_docx:
        try:
            docx_path = await write_md_to_word(report, task_id)
            if docx_path:
                print(f"DOCX written to '{docx_path}'")
        except Exception as e:
            print(f"Warning: DOCX generation failed: {e}")

if __name__ == "__main__":
    load_dotenv()
    args = cli.parse_args()
    asyncio.run(main(args))
