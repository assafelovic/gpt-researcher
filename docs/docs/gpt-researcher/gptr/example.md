# Agent-Beispiel

Wenn du GPT Researcher als eigenständigen Agenten nutzen möchtest, kannst du ihn ganz einfach in ein bestehendes Python-Projekt importieren. Unten findest du ein Beispiel, das den Agenten aufruft, um einen Research-Report zu erzeugen:

```python
from gpt_researcher import GPTResearcher
import asyncio

async def fetch_report(query):
    """
    Holt einen Research-Report auf Basis der übergebenen Anfrage.
    """
    researcher = GPTResearcher(query=query)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

async def generate_research_report(query):
    """
    Dieses Beispielskript führt eine asynchrone Main-Funktion aus,
    um einen Research-Report zu erzeugen.
    """
    report = await fetch_report(query)
    print(report)

if __name__ == "__main__":
    QUERY = "Was ist bei den letzten Burning-Man-Überschwemmungen passiert?"
    asyncio.run(generate_research_report(query=QUERY))
```

Du kannst dieses Beispiel leicht erweitern und den zurückgegebenen Report als Kontext für nützliche Inhalte wie News-Artikel, Marketingtexte, E-Mail-Vorlagen, Newsletter und mehr verwenden.

Außerdem kannst du GPT Researcher nutzen, um Informationen zu Code-Dokumentation, Business-Analysen, Finanzdaten und vielem mehr zu sammeln. So lassen sich auch deutlich komplexere Aufgaben mit faktenbasierten und hochwertigen Echtzeitinformationen lösen.
