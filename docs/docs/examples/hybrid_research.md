# Hybride Recherche

## Einführung

GPT Researcher kann Websuche und lokale Dokumentenanalyse kombinieren, um umfassende und kontextbewusste Rechercheergebnisse zu liefern.

Dieser Leitfaden zeigt dir, wie du Hybrid Research mit GPT Researcher einrichtest und ausführst.

## Voraussetzungen

Bevor du startest, stelle sicher, dass du Folgendes hast:

- Python 3.10 oder neuer
- pip
- Einen OpenAI-API-Key oder ein anderes unterstütztes LLM
- Optional einen Web-Retriever. DuckDuckGo ist Standard, Tavily funktioniert, wenn `TAVILY_API_KEY` gesetzt ist.

## Installation

```bash
pip install gpt-researcher
```

## Umgebung einrichten

Setze deine API-Keys als Umgebungsvariablen:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
# Optional: den DuckDuckGo-Standard mit Tavily oder einem anderen Retriever überschreiben
# export TAVILY_API_KEY=your_tavily_api_key_here
```

Für eigene OpenAI-kompatible APIs kannst du auch setzen:

```bash
export OPENAI_BASE_URL=your_custom_api_base_url_here
```

Alternativ kannst du die Werte auch direkt in deinem Python-Skript setzen:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your_openai_api_key_here'
# os.environ['TAVILY_API_KEY'] = 'your_tavily_api_key_here'
os.environ['OPENAI_BASE_URL'] = 'your_custom_api_base_url_here'
```

## Dokumente vorbereiten

### 1. Lokale Dokumente
1. Erstelle im Projektordner ein Verzeichnis namens `my-docs`.
2. Lege dort alle relevanten lokalen Dokumente ab, zum Beispiel PDFs, TXT-, DOCX- oder CSV-Dateien.

### 2. Online-Dokumente
1. Nutze Online-Dokument-URLs, zum Beispiel `https://xxxx.xxx.pdf` - unterstützt werden Formate wie PDFs, TXTs und DOCXs.

## Hybrid Research mit lokalen Dokumenten

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_research_report(query: str, report_type: str, report_source: str) -> str:
    researcher = GPTResearcher(query=query, report_type=report_type, report_source=report_source)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "Wie unterscheidet sich unsere Produkt-Roadmap von den Markttrends in unserer Branche?"
    report_source = "hybrid"

    report = asyncio.run(get_research_report(query=query, report_type="research_report", report_source=report_source))
    print(report)
```

## Hybrid Research mit Online-Dokumenten

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_research_report(query: str, report_type: str, report_source: str) -> str:
    researcher = GPTResearcher(query=query, report_type=report_type, document_urls=document_urls, report_source=report_source)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    query = "Wie unterscheidet sich unsere Produkt-Roadmap von den Markttrends in unserer Branche?"
    report_source = "hybrid"
    document_urls = ["https://xxxx.xxx.pdf", "https://xxxx.xxx.doc"]

    report = asyncio.run(get_research_report(query=query, report_type="research_report", document_urls=document_urls, report_source=report_source))
    print(report)
```

## Ausführen

1. Als `run_research.py` speichern
2. Mit `python run_research.py` ausführen

## Ergebnisse verstehen

Der Output ist ein umfassender Research-Report, der Erkenntnisse aus Webquellen und lokalen Dokumenten kombiniert. Der Report enthält typischerweise eine Zusammenfassung, wichtige Ergebnisse, eine detaillierte Analyse, Vergleiche zwischen internen Daten und externen Trends sowie Empfehlungen.

## Fehlerbehebung

1. **API-Key-Probleme**: Prüfe, ob deine API-Keys korrekt gesetzt sind.
2. **Dokumentenladefehler**: Prüfe, ob die lokalen Dokumente in unterstützten Formaten vorliegen und nicht beschädigt sind.
3. **Speicherprobleme**: Bei großen Dokumenten oder umfangreicher Recherche kann mehr Arbeitsspeicher nötig sein.

## FAQ

**F: Wie lange dauert eine typische Recherche?**
**A:** Das hängt von der Komplexität und der Datenmenge ab. Für sehr umfangreiche Recherchen können es 1-5 Minuten sein.

**F: Kann ich GPT Researcher mit anderen Sprachmodellen verwenden?**
**A:** Aktuell ist GPT Researcher für OpenAI-Modelle optimiert. Unterstützung für andere Modelle findest du in der LLM-Dokumentation.

**F: Wie geht GPT Researcher mit widersprüchlichen Informationen um?**
**A:** Das System versucht, Unterschiede durch Kontext und Hinweise auf Abweichungen im finalen Report sichtbar zu machen.

**F: Werden lokale Daten an externe Server gesendet?**
**A:** Nein, lokale Dokumente werden auf deiner Maschine verarbeitet. Nur erzeugte Suchanfragen und zusammengefasste Informationen werden für die Webrecherche an externe Dienste gesendet.

Weitere Informationen und Updates findest du im [GPT-Researcher-GitHub-Repository](https://github.com/assafelovic/gpt-researcher).
