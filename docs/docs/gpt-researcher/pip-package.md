# PIP Package

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


async def get_report(query: str, report_type: str) -> str:
    researcher = GPTResearcher(query, report_type)
    report = await researcher.run()
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
async def get_report(report_type: str, query: str):
    researcher = GPTResearcher(query, report_type)
    report = await researcher.run()
    return {"report": report}

# Run the server
# uvicorn main:app --reload
```

### Flask Example
```python
from flask import Flask, request
from gpt_researcher import GPTResearcher
import asyncio

app = Flask(__name__)

@app.route('/report/<report_type>', methods=['GET'])
def get_report(report_type):
    query = request.args.get('query')
    report = asyncio.run(GPTResearcher(query, report_type).run())
    return report

# Run the server
# flask run
```

