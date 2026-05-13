# Detaillierter Report

## Überblick

Die Klasse `DetailedReport` ist vom STORM-Paper inspiriert und ein leistungsstarker Bestandteil von GPT Researcher. Sie wurde entwickelt, um umfassende Reports zu komplexen Themen zu erzeugen. Besonders nützlich ist sie für Long-Form-Inhalte, die über die typischen Grenzen von LLM-Ausgaben hinausgehen. Die Klasse zerlegt eine Hauptanfrage in Unterthemen, recherchiert diese im Detail und setzt die Ergebnisse zu einem zusammenhängenden, ausführlichen Report zusammen.

Die Klasse liegt im [GPT-Researcher-GitHub-Repository](https://github.com/assafelovic/gpt-researcher) unter `backend/report_type/detailed_report.py` und nutzt den `GPTResearcher`-Agenten, um gezielt zu recherchieren und Inhalte zu erzeugen.

## Wichtige Funktionen

- Zerlegt komplexe Themen in handhabbare Unterthemen
- Recherchiert jedes Unterthema im Detail
- Erzeugt einen umfassenden Report mit Einleitung, Inhaltsverzeichnis und Hauptteil
- Vermeidet Redundanz durch das Verfolgen bereits geschriebener Inhalte
- Unterstützt asynchrone Abläufe für bessere Performance

## Klassenstruktur

### Initialisierung

Die Klasse `DetailedReport` wird mit diesen Parametern initialisiert:

- `query`: Die Haupt-Research-Frage
- `report_type`: Der Report-Typ
- `report_source`: Die Quelle des Reports
- `source_urls`: Anfangsliste von Quell-URLs
- `config_path`: Pfad zur Konfigurationsdatei
- `tone`: Ton des Reports
- `websocket`: WebSocket für Echtzeitkommunikation
- `subtopics`: Optionale Liste vorgegebener Unterthemen
- `headers`: Optionale HTTP-Header

## Funktionsweise

1. Die Klasse startet mit einer ersten Recherche zur Hauptfrage.
2. Danach zerlegt sie das Thema in Unterthemen.
3. Für jedes Unterthema:
   - wird fokussiert recherchiert
   - werden Entwurfstitel erzeugt
   - wird bereits geschriebener Kontext abgerufen, um Redundanz zu vermeiden
   - wird ein Report-Abschnitt geschrieben
4. Am Ende werden alle Unterberichte kombiniert, ein Inhaltsverzeichnis hinzugefügt und Quellenangaben eingebunden.

## Beispiel

```python
import asyncio
from fastapi import WebSocket
from gpt_researcher.utils.enum import Tone
from backend.report_type import DetailedReport

async def generate_report(websocket: WebSocket):
    detailed_report = DetailedReport(
        query="Die Auswirkungen künstlicher Intelligenz auf das moderne Gesundheitswesen",
        report_type="research_report",
        report_source="web_search",
        source_urls=[],
        config_path="path/to/config.yaml",
        tone=Tone.FORMAL,
        websocket=websocket,
        subtopics=[],
        headers={}
    )

    final_report = await detailed_report.run()
    return final_report

@app.websocket("/generate_report")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    report = await generate_report(websocket)
    await websocket.send_text(report)
```

Dieses Beispiel zeigt, wie du eine `DetailedReport`-Instanz erzeugst und einen ausführlichen Report zum Einfluss von KI auf das Gesundheitswesen generierst.

## Fazit

Die Klasse `DetailedReport` ist ein anspruchsvolles Werkzeug für tiefgehende, gut strukturierte Reports zu komplexen Themen. Durch das Aufteilen der Hauptfrage in Unterthemen und die Nutzung von GPT Researcher kann sie Inhalte erzeugen, die weit über die typischen Grenzen von LLM-Ausgaben hinausgehen. Damit ist sie ein wertvolles Werkzeug für Forschende, Content-Ersteller und alle, die detaillierte, gut recherchierte Informationen brauchen.
