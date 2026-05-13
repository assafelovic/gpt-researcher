# LangGraph

[LangGraph](https://python.langchain.com/docs/langgraph) ist eine Bibliothek für zustandsbehaftete Multi-Agent-Anwendungen mit LLMs.
Dieses Beispiel nutzt LangGraph, um den Rechercheprozess für ein beliebiges Thema zu automatisieren.

## Anwendungsfall

Mit LangGraph lässt sich der Rechercheprozess deutlich in Tiefe und Qualität verbessern, weil mehrere Agenten mit spezialisierten Fähigkeiten zusammenarbeiten.
Inspiriert von der [STORM](https://arxiv.org/abs/2402.14207)-Arbeit zeigt dieses Beispiel, wie ein Team von KI-Agenten ein Thema von der Planung bis zur Veröffentlichung bearbeitet.

Ein durchschnittlicher Lauf erzeugt einen 5- bis 6-seitigen Research-Report in mehreren Formaten wie PDF, DOCX und Markdown.

Hinweis: Dieses Beispiel verwendet die OpenAI-API nur für eine optimierte Performance.

## Das Multi-Agent-Team

Das Rechercheteam besteht aus 7 KI-Agenten:
- **Human** - Der Mensch im Loop, der den Prozess überwacht und Feedback gibt
- **Chief Editor** - Überwacht den Prozess und koordiniert das Team
- **Researcher** (`gpt-researcher`) - Ein spezialisierter autonomer Agent für tiefgehende Recherche
- **Editor** - Plant Gliederung und Struktur des Reports
- **Reviewer** - Prüft die Korrektheit der Ergebnisse anhand definierter Kriterien
- **Revisor** - Überarbeitet die Ergebnisse anhand des Feedbacks
- **Writer** - Schreibt den finalen Report
- **Publisher** - Veröffentlicht den finalen Report in verschiedenen Formaten

## So funktioniert es

Der Ablauf besteht im Wesentlichen aus diesen Phasen:
1. Planungsphase
2. Datensammlung und Analyse
3. Review und Überarbeitung
4. Schreiben und Einreichen
5. Veröffentlichung

### Architektur

<div align="center">
<img align="center" height="600" src="https://cowriter-images.s3.amazonaws.com/multi-agents-gptr.png"></img>
</div>
<br clear="all"/>

### Schritte

Im Detail läuft der Prozess so ab:
- Browser (`gpt-researcher`) durchsucht das Internet für die erste Recherche
- Der Editor plant auf Basis der ersten Ergebnisse die Struktur des Reports
- Für jedes Gliederungsthema parallel:
  - Der Researcher recherchiert tief in den Unterthemen und schreibt einen Entwurf
  - Der Reviewer prüft die Korrektheit des Entwurfs und gibt Feedback
  - Der Revisor verbessert den Entwurf anhand dieses Feedbacks
- Der Writer erstellt den finalen Report inklusive Einleitung, Fazit und Quellen
- Der Publisher gibt den finalen Report in mehreren Formaten aus, zum Beispiel PDF, DOCX oder Markdown

## So startest du es

1. Benötigte Pakete installieren:
    ```bash
    pip install -r requirements.txt
    ```
2. Umgebungsvariablen setzen:
   ```bash
   export OPENAI_API_KEY={Your OpenAI API Key here}
   export TAVILY_API_KEY={Your Tavily API Key here}
   ```
3. Anwendung starten:
    ```bash
    python main.py
    ```

## Nutzung

Wenn du die Forschungsfrage oder den Report anpassen willst, bearbeite die Datei `task.json` im Hauptverzeichnis.

#### `task.json` enthält diese Felder:
- `query` - Die Forschungsfrage oder Aufgabe
- `model` - Das für die Agenten zu nutzende OpenAI-LLM
- `max_sections` - Maximale Anzahl an Abschnitten im Report
- `include_human_feedback` - Wenn `true`, kann der Nutzer Feedback geben
- `publish_formats` - Formate, in denen der Report veröffentlicht wird
- `source` - Die Quelle für die Recherche (`web` oder `local`)
- `follow_guidelines` - Wenn `true`, werden die unten definierten Leitlinien befolgt
- `guidelines` - Liste von Leitlinien für den Report
- `verbose` - Wenn `true`, werden detaillierte Logs auf der Konsole ausgegeben

#### Beispiel:
```json
{
  "query": "Ist KI in einer Hype-Phase?",
  "model": "gpt-4o",
  "max_sections": 3,
  "publish_formats": {
    "markdown": true,
    "pdf": true,
    "docx": true
  },
  "include_human_feedback": false,
  "source": "web",
  "follow_guidelines": true,
  "guidelines": [
    "Der Report MUSS die ursprüngliche Frage vollständig beantworten",
    "Der Report MUSS im APA-Format geschrieben sein",
    "Der Report MUSS auf Englisch geschrieben sein"
  ],
  "verbose": true
}
```

## Bereitstellen

```shell
pip install langgraph-cli
langgraph up
```

Mehr dazu findest du [hier](https://github.com/langchain-ai/langgraph-example), insbesondere zu Streaming-, Async-Endpunkten und dem Playground.

## NextJS-Frontend-App

Die React-App im `frontend`-Verzeichnis ist unsere Frontend-2.0-Version. Sie soll die Stärke des Backends auch im Frontend sichtbar machen.

Sie bringt viele zusätzliche Funktionen mit, zum Beispiel:
- Drag-and-Drop-Oberfläche zum Hochladen und Löschen von Dateien für lokale Dokumente
- GUI zum Setzen deiner GPTR-Umgebungsvariablen
- Möglichkeit, den Multi-Agents-Flow über das Backend-Modul oder den LangGraph-Cloud-Host auszulösen
- Stabilitätsverbesserungen

### NextJS-React-App mit Docker starten

> **Schritt 1** - [Docker installieren](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Schritt 2** - Die `.env.example` kopieren, API-Keys eintragen und als `.env` speichern

> **Schritt 3** - In der `docker-compose`-Datei die Services auskommentieren, die du nicht mit Docker starten willst

```bash
$ docker-compose up --build
```

> **Schritt 4** - Wenn du nichts auskommentiert hast, starten standardmäßig zwei Prozesse:
 - der Python-Server auf `localhost:8000`
 - die React-App auf `localhost:3000`

Öffne `localhost:3000` im Browser und leg los.

### NextJS-React-App mit NPM starten

```bash
cd frontend/nextjs
nvm install 18.17.0
nvm use v18.17.0
npm install --legacy-peer-deps
npm run dev
```
