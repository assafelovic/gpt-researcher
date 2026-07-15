"""
Markdown Report Generator
-------------------------
Runs GPT-Researcher on one or more queries and saves each report as a
timestamped Markdown file in outputs/.

Usage:
    # Single query
    python -m evals.report_generator.run --query "What caused the 2008 financial crisis?"

    # Batch from JSONL file
    python -m evals.report_generator.run --file evals/report_generator/queries.jsonl

    # Limit batch size
    python -m evals.report_generator.run --file queries.jsonl --limit 3
"""

import asyncio
import argparse
import json
import re
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone

OUTPUT_DIR = Path(__file__).parent / "outputs"


def _slugify(text: str, max_len: int = 50) -> str:
    """Convert query to a safe filename slug."""
    slug = re.sub(r'[^\w\s-]', '', text[:max_len])
    return slug.strip().replace(' ', '_').lower()


async def generate_report(query: str, output_dir: Path) -> Path:
    """Run researcher on a single query and save as .md file."""
    print(f"\n>> Generating report for: {query}")

    researcher = GPTResearcher(
        query=query,
        report_type=ReportType.ResearchReport.value,
        report_format="markdown",
        report_source=ReportSource.Web.value,
        tone=Tone.Objective,
        verbose=False,
    )
    await researcher.conduct_research()
    report = await researcher.write_report()

    sources   = researcher.get_source_urls()
    cost      = researcher.get_costs()
    timestamp = datetime.now()

    filename = output_dir / f"{timestamp:%Y%m%d_%H%M%S}_{_slugify(query)}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {query}\n\n")
        f.write(f"*Generated: {timestamp.isoformat()}*  \n")
        f.write(f"*Sources: {len(sources)}  |  Cost: ${cost:.4f}*\n\n")
        f.write("---\n\n")
        f.write(report)
        f.write("\n\n---\n\n## Sources\n\n")
        for url in sources:
            f.write(f"- {url}\n")

    print(f"   Saved → {filename.name}  ({len(sources)} sources, ${cost:.4f})")
    return filename


async def main(queries: list[str], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for query in queries:
        try:
            path = await generate_report(query, output_dir)
            saved.append(path)
        except Exception as e:
            print(f"   [ERROR] {query}: {e}")

    print(f"\nDone. {len(saved)}/{len(queries)} reports saved to {output_dir}")


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate Markdown research reports")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", type=str,
                       help="Single research query")
    group.add_argument("--file",  type=str,
                       help="JSONL file with {\"question\": ...} entries")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of queries to process (batch mode)")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR),
                        help="Directory to save reports")
    args = parser.parse_args()

    if args.query:
        queries = [args.query]
    else:
        queries = []
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                queries.append(data["question"])
        if args.limit:
            queries = queries[:args.limit]

    asyncio.run(main(queries, Path(args.output_dir)))
