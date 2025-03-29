# Simple Run

### Run PIP Package
```python
from gpt_researcher import GPTResearcher
import asyncio

### Using Quick Run
async def main():
    """
    This is a sample script that shows how to run a research report.
    """
    # Query
    query = "What happened in the latest burning man floods?"

    # Report Type
    report_type = "research_report"

    # Initialize the researcher
    researcher = GPTResearcher(query=query, report_type=report_type, config_path=None)
    # Conduct research on the given query
    await researcher.conduct_research()
    # Write the report
    report = await researcher.write_report()
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

# Custom Report Formatting

### Using Custom Prompts
```python
from gpt_researcher import GPTResearcher
import asyncio


async def main():
    """
    This example shows how to use custom prompts to control report formatting.
    """
    # Query
    query = "What are the latest advancements in renewable energy?"

    # Report Type
    report_type = "research_report"

    # Initialize the researcher
    researcher = GPTResearcher(query=query, report_type=report_type)
    
    # Conduct research on the given query
    await researcher.conduct_research()
    
    # Generate a standard report
    standard_report = await researcher.write_report()
    print("Standard Report Generated")
    
    # Generate a short, concise report using custom_prompt
    custom_prompt = "Provide a concise summary in 2 paragraphs without citations."
    short_report = await researcher.write_report(custom_prompt=custom_prompt)
    print("Short Report Generated")
    
    # Generate a bullet-point format report
    bullet_prompt = "List the top 5 advancements as bullet points with brief explanations."
    bullet_report = await researcher.write_report(custom_prompt=bullet_prompt)
    print("Bullet-Point Report Generated")
    
    return standard_report, short_report, bullet_report


if __name__ == "__main__":
    asyncio.run(main())

For more comprehensive examples of using custom prompts, see the `custom_prompt.py` file included in the examples directory.
```