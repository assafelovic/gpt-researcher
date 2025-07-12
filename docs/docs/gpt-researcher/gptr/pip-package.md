# PIP Package
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)

🌟 **Exciting News!** Now, you can integrate `gpt-researcher` with your apps seamlessly!

## Steps to Install GPT Researcher

Follow these easy steps to get started:

0. **Pre-requisite**: Ensure Python 3.10+ is installed on your machine 💻
1. **Install gpt-researcher**: Grab the official package from [PyPi](https://pypi.org/project/gpt-researcher/).

```bash
pip install gpt-researcher
```

2. **Environment Variables:** Create a .env file with your OpenAI API key or simply export it

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
```

```bash
export TAVILY_API_KEY={Your Tavily API Key here}
```

3. **Start using GPT Researcher in your own codebase**

## Example Usage

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_report(query: str, report_type: str):
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Get additional information
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return report, research_context, research_costs, research_images, research_sources

if __name__ == "__main__":
    query = "what team may win the NBA finals?"
    report_type = "research_report"

    report, context, costs, images, sources = asyncio.run(get_report(query, report_type))
    
    print("Report:")
    print(report)
    print("\nResearch Costs:")
    print(costs)
    print("\nNumber of Research Images:")
    print(len(images))
    print("\nNumber of Research Sources:")
    print(len(sources))
```

## Specific Examples

### Example 1: Research Report

```python
query = "Latest developments in renewable energy technologies"
report_type = "research_report"
```

### Example 2: Resource Report

```python
query = "List of top AI conferences in 2023"
report_type = "resource_report"
```

### Example 3: Outline Report

```python
query = "Outline for an article on the impact of AI in education"
report_type = "outline_report"
```

## Integration with Web Frameworks

### FastAPI Example

```python
from fastapi import FastAPI
from gpt_researcher import GPTResearcher
import asyncio

app = FastAPI()

@app.get("/report/{report_type}")
async def get_report(query: str, report_type: str) -> dict:
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    source_urls = researcher.get_source_urls()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return {
        "report": report,
        "source_urls": source_urls,
        "research_costs": research_costs,
        "num_images": len(research_images),
        "num_sources": len(research_sources)
    }

# Run the server
# uvicorn main:app --reload
```

### Flask Example

**Pre-requisite**: Install flask with the async extra.

```bash
pip install 'flask[async]'
```

```python
from flask import Flask, request, jsonify
from gpt_researcher import GPTResearcher

app = Flask(__name__)

@app.route('/report/<report_type>', methods=['GET'])
async def get_report(report_type):
    query = request.args.get('query')
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    source_urls = researcher.get_source_urls()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return jsonify({
        "report": report,
        "source_urls": source_urls,
        "research_costs": research_costs,
        "num_images": len(research_images),
        "num_sources": len(research_sources)
    })

# Run the server
# flask run
```

**Run the server**

```bash
flask run
```

**Example Request**

```bash
curl -X GET "http://localhost:5000/report/research_report?query=what team may win the nba finals?"
```

## Getters and Setters
GPT Researcher provides several methods to retrieve additional information about the research process:

### Get Research Sources
Sources are the URLs that were used to gather information for the research.
```python
source_urls = researcher.get_source_urls()
```

### Get Research Context
Context is all the retrieved information from the research. It includes the sources and their corresponding content.
```python
research_context = researcher.get_research_context()
```

### Get Research Costs
Costs are the number of tokens consumed during the research process.
```python
research_costs = researcher.get_costs()
```

### Get Research Images
Retrieves a list of images found during the research process.
```python
research_images = researcher.get_research_images()
```

### Get Research Sources
Retrieves a list of research sources, including title, content, and images.
```python
research_sources = researcher.get_research_sources()
```

### Set Verbose
You can set the verbose mode to get more detailed logs.
```python
researcher.set_verbose(True)
```

### Add Costs
You can also add costs to the research process if you want to track the costs from external usage.
```python
researcher.add_costs(0.22)
```

## Advanced Usage

### Customizing the Research Process

You can customize various aspects of the research process by passing additional parameters when initializing the GPTResearcher:

```python
researcher = GPTResearcher(
    query="Your research query",
    report_type="research_report",
    report_format="APA",
    tone="formal and objective",
    max_subtopics=5,
    verbose=True
)
```

### Handling Research Results

After conducting research, you can process the results in various ways:

```python
# Conduct research
research_result = await researcher.conduct_research()

# Generate a standard report
report = await researcher.write_report()

# Generate a customized report with specific formatting requirements
custom_report = await researcher.write_report(custom_prompt="Answer in short, 2 paragraphs max without citations.")

# Generate a focused report for a specific audience
executive_summary = await researcher.write_report(custom_prompt="Create an executive summary focused on business impact and ROI. Keep it under 500 words.")

# Generate a report with specific structure requirements
technical_report = await researcher.write_report(custom_prompt="Create a technical report with problem statement, methodology, findings, and recommendations sections.")

# Generate a conclusion
conclusion = await researcher.write_report_conclusion(report)

# Get subtopics
subtopics = await researcher.get_subtopics()

# Get draft section titles for a subtopic
draft_titles = await researcher.get_draft_section_titles("Subtopic name")
```

### Customizing Report Generation with Custom Prompts

The `write_report` method accepts a `custom_prompt` parameter that gives you complete control over how your research is presented:

```python
# After conducting research
research_result = await researcher.conduct_research()

# Generate a report with a custom prompt
report = await researcher.write_report(
    custom_prompt="Based on the research, provide a bullet-point summary of the key findings."
)
```

Custom prompts can be used for various purposes:

1. **Format Control**: Specify the structure, length, or style of your report
   ```python
   report = await researcher.write_report(
       custom_prompt="Write a blog post in a conversational tone using the research. Include headings and a conclusion."
   )
   ```

2. **Audience Targeting**: Tailor the content for specific readers
   ```python
   report = await researcher.write_report(
       custom_prompt="Create a report for technical stakeholders, focusing on methodologies and implementation details."
   )
   ```

3. **Specialized Outputs**: Generate specific types of content
   ```python
   report = await researcher.write_report(
       custom_prompt="Create a FAQ section based on the research with at least 5 questions and detailed answers."
   )
   ```

The custom prompt will be combined with the research context to generate your customized report.

### Working with Research Context

You can use the research context for further processing or analysis:

```python
# Get the full research context
context = researcher.get_research_context()

# Get similar written contents based on draft section titles
similar_contents = await researcher.get_similar_written_contents_by_draft_section_titles(
    current_subtopic="Subtopic name",
    draft_section_titles=["Title 1", "Title 2"],
    written_contents=some_written_contents,
    max_results=10
)
```

This comprehensive documentation should help users understand and utilize the full capabilities of the GPT Researcher package.
