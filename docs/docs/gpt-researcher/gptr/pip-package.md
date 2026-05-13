# PIP-Paket
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)

🌟 **Gute Nachricht!** Du kannst `gpt-researcher` jetzt nahtlos in deine Anwendungen integrieren.

## Schritte zur Installation von GPT Researcher

Folge diesen einfachen Schritten, um loszulegen:

0. **Voraussetzung**: Stelle sicher, dass Python 3.10+ auf deinem Rechner installiert ist 💻
1. **gpt-researcher installieren**: Hol dir das offizielle Paket von [PyPI](https://pypi.org/project/gpt-researcher/).

```bash
pip install gpt-researcher
```

2. **Umgebungsvariablen:** Lege eine `.env`-Datei mit deinem OpenAI-API-Key an oder exportiere den Key direkt. Für Websuche wird standardmäßig DuckDuckGo verwendet, sofern du keinen anderen Retriever konfigurierst.

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
# Optional: Retriever-API-Key setzen, wenn du den DuckDuckGo-Standard überschreiben möchtest.
# export TAVILY_API_KEY={Your Tavily API Key here}
```

3. **GPT Researcher in deinem eigenen Code einsetzen**

## Example Usage

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_report(query: str, report_type: str):
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Zusätzliche Informationen abrufen
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
    print("\nResearch-Kosten:")
    print(costs)
    print("\nAnzahl der Research-Bilder:")
    print(len(images))
    print("\nAnzahl der Research-Quellen:")
    print(len(sources))
```

## Konkrete Beispiele

### Beispiel 1: Research-Report

```python
query = "Latest developments in renewable energy technologies"
report_type = "research_report"
```

### Beispiel 2: Quellen-Report

```python
query = "List of top AI conferences in 2023"
report_type = "resource_report"
```

### Beispiel 3: Gliederungs-Report

```python
query = "Outline for an article on the impact of AI in education"
report_type = "outline_report"
```

## Integration mit Web-Frameworks

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

    # Server starten
# uvicorn main:app --reload
```

### Flask Example

**Voraussetzung**: Flask mit dem Async-Extra installieren.

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

    # Server starten
# flask run
```

**Server starten**

```bash
flask run
```

**Beispielanfrage**

```bash
curl -X GET "http://localhost:5000/report/research_report?query=what team may win the nba finals?"
```

## Getter und Setter
GPT Researcher stellt mehrere Methoden bereit, um zusätzliche Informationen zum Research-Prozess abzurufen:

### Research-Quellen abrufen
Quellen sind die URLs, die für die Recherche verwendet wurden.
```python
source_urls = researcher.get_source_urls()
```

### Research-Kontext abrufen
Der Kontext umfasst alle während der Recherche gesammelten Informationen, einschließlich Quellen und zugehöriger Inhalte.
```python
research_context = researcher.get_research_context()
```

### Research-Kosten abrufen
Die Kosten entsprechen der Anzahl der Tokens, die während des Research-Prozesses verbraucht wurden.
```python
research_costs = researcher.get_costs()
```

### Research-Bilder abrufen
Liefert eine Liste der Bilder, die während der Recherche gefunden wurden.
```python
research_images = researcher.get_research_images()
```

### Research-Quellen abrufen
Liefert eine Liste der Research-Quellen inklusive Titel, Inhalt und Bildern.
```python
research_sources = researcher.get_research_sources()
```

### Verbose-Modus setzen
Du kannst den Verbose-Modus aktivieren, um ausführlichere Logs zu erhalten.
```python
researcher.set_verbose(True)
```

### Kosten hinzufügen
Du kannst dem Research-Prozess auch Kosten hinzufügen, wenn du Ausgaben aus externer Nutzung mittracken möchtest.
```python
researcher.add_costs(0.22)
```

## Erweiterte Nutzung

### Den Research-Prozess anpassen

Du kannst verschiedene Aspekte des Research-Prozesses anpassen, indem du bei der Initialisierung von `GPTResearcher` zusätzliche Parameter übergibst:

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

### Research-Ergebnisse verarbeiten

Nach der Recherche kannst du die Ergebnisse auf verschiedene Arten weiterverarbeiten:

```python
# Recherche durchführen
research_result = await researcher.conduct_research()

# Standard-Report erzeugen
report = await researcher.write_report()

# Angepassten Report mit speziellen Formatierungsanforderungen erzeugen
custom_report = await researcher.write_report(custom_prompt="Answer in short, 2 paragraphs max without citations.")

# Einen fokussierten Report für ein bestimmtes Publikum erzeugen
executive_summary = await researcher.write_report(custom_prompt="Create an executive summary focused on business impact and ROI. Keep it under 500 words.")

# Einen Report mit spezieller Struktur erzeugen
technical_report = await researcher.write_report(custom_prompt="Create a technical report with problem statement, methodology, findings, and recommendations sections.")

# Ein Fazit erzeugen
conclusion = await researcher.write_report_conclusion(report)

# Unterthemen abrufen
subtopics = await researcher.get_subtopics()

# Entwurfstitel für ein Unterthema abrufen
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
