"""
Custom Prompt Example for GPT Researcher

This example demonstrates how to use the custom_prompt parameter to customize report generation
based on specific formatting requirements or content needs.
"""

import asyncio
import nest_asyncio  # Required for notebooks/interactive environments

# Apply nest_asyncio to allow for nested event loops (needed in notebooks)
nest_asyncio.apply()

from gpt_researcher import GPTResearcher


async def custom_report_example():
    """Demonstrate various custom prompt examples with GPT Researcher."""
    
    # Define your research query
    query = "What are the latest advancements in renewable energy?"
    report_type = "research_report"
    
    # Initialize the researcher
    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        verbose=True  # Set to True to see detailed logs
    )
    
    # Conduct the research (this step is the same regardless of custom prompts)
    print("🔍 Conducting research...")
    await researcher.conduct_research()
    print("✅ Research completed!\n")
    
    # Example 1: Standard report (no custom prompt)
    print("\n📝 EXAMPLE 1: STANDARD REPORT\n" + "="*40)
    standard_report = await researcher.write_report()
    print(f"Standard Report Length: {len(standard_report.split())} words\n")
    print(standard_report[:500] + "...\n")  # Print first 500 chars
    
    # Example 2: Short summary with custom prompt
    print("\n📝 EXAMPLE 2: SHORT SUMMARY\n" + "="*40)
    short_prompt = "Provide a brief summary of the research findings in 2-3 paragraphs without citations."
    short_report = await researcher.write_report(custom_prompt=short_prompt)
    print(f"Short Report Length: {len(short_report.split())} words\n")
    print(short_report + "\n")
    
    # Example 3: Bullet point format
    print("\n📝 EXAMPLE 3: BULLET POINT FORMAT\n" + "="*40)
    bullet_prompt = "List the top 5 advancements in renewable energy as bullet points with a brief explanation for each."
    bullet_report = await researcher.write_report(custom_prompt=bullet_prompt)
    print(bullet_report + "\n")
    
    # Example 4: Question and answer format
    print("\n📝 EXAMPLE 4: Q&A FORMAT\n" + "="*40)
    qa_prompt = "Present the research as a Q&A session with 5 important questions and detailed answers about renewable energy advancements."
    qa_report = await researcher.write_report(custom_prompt=qa_prompt)
    print(qa_report[:500] + "...\n")  # Print first 500 chars
    
    # Example 5: Technical audience
    print("\n📝 EXAMPLE 5: TECHNICAL AUDIENCE\n" + "="*40)
    technical_prompt = "Create a technical summary focusing on engineering challenges and solutions in renewable energy. Use appropriate technical terminology."
    technical_report = await researcher.write_report(custom_prompt=technical_prompt)
    print(technical_report[:500] + "...\n")  # Print first 500 chars
    
    # Show research costs
    print("\n💰 RESEARCH COSTS")
    print(f"Total tokens used: {researcher.get_costs()}")


if __name__ == "__main__":
    asyncio.run(custom_report_example())
