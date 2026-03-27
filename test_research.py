"""Quick test — run a single research query and print the report."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from gpt_researcher import GPTResearcher


async def main():
    query = "What are the top WooCommerce performance optimization strategies in 2025?"

    print(f"\n🔍 Researching: {query}\n{'='*60}\n")

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        verbose=True,
    )

    await researcher.conduct_research()
    report = await researcher.write_report()

    print("\n" + "="*60)
    print("REPORT")
    print("="*60)
    print(report)

    # Save to file
    with open("output_report.md", "w") as f:
        f.write(report)
    print("\n✅ Saved to output_report.md")


if __name__ == "__main__":
    asyncio.run(main())
