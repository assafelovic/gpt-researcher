# PIP Package
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/examples/pip-run.ipynb)

🌟 **Exciting News!** Now, you can integrate `gpt-researcher` with your apps seamlessly!

## Steps to Install GPT Researcher 🛠️

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

## Example Usage 📝

```python
from gpt_researcher import GPTResearcher
import asyncio


from gpt_researcher import GPTResearcher
import asyncio


async def get_report(query: str, report_type: str) -> str:
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "what team may win the NBA finals?"
    report_type = "research_report"

    report = asyncio.run(get_report(query, report_type))
    print(report)
```

## Specific Examples 🌐

### Example 1: Research Report 📚

```python
query = "Latest developments in renewable energy technologies"
report_type = "research_report"
```

### Example 2: Resource Report 📋

```python
query = "List of top AI conferences in 2023"
report_type = "resource_report"
```

### Example 3: Outline Report 📝

```python
query = "Outline for an article on the impact of AI in education"
report_type = "outline_report"
```

## Integration with Web Frameworks 🌍

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
    return {"report": report}

# Run the server
# uvicorn main:app --reload
```

### Flask Example

**Pre-requisite**: Install flask with the async extra.

```bash
pip install 'flask[async]'
```

```python
from flask import Flask, request
from gpt_researcher import GPTResearcher

app = Flask(__name__)

@app.route('/report/<report_type>', methods=['GET'])
async def get_report(report_type):
    query = request.args.get('query')
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report

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

**Note**: The above code snippets are just examples. You can customize them as per your requirements.
