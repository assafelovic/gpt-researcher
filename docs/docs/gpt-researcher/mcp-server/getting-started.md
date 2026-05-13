---
sidebar_position: 1
---

# Erste Schritte

Der GPT-Researcher-MCP-Server bringt Model Context Protocol (MCP) in GPT Researcher. Damit können KI-Assistenten autonome, umfassende Webrecherchen durchführen und über MCP Reports erzeugen.

## Warum GPT Researcher MCP?

Viele KI-Apps können über MCP auf Websuche zugreifen, aber GPT Researcher MCP liefert tiefere Ergebnisse. Normale Suchwerkzeuge geben rohe Treffer zurück, die man manuell filtern muss und die oft irrelevante Quellen enthalten.

GPT Researcher führt autonome, tiefe Recherchen durch - nicht nur einfache Suchen. Das System erkundet und validiert mehrere Quellen intelligent, konzentriert sich auf relevante und aktuelle Informationen und liefert trotz etwas höherer Laufzeit meist bessere Resultate.

Der MCP-Server stellt diesen Fähigkeiten folgende Funktionen zur Verfügung:

### Ressourcen
- `research_resource`: Liefert Webressourcen zu einer Aufgabe über Recherche

### Hauptwerkzeuge
- `deep_research`: Führt autonome Webrecherche zu einem Thema aus
- `quick_search`: Führt eine schnelle Websuche aus und gibt Treffer mit Snippets zurück
- `write_report`: Erzeugt einen Report aus den Rechercheergebnissen
- `get_research_sources`: Liefert die in der Recherche verwendeten Quellen
- `get_research_context`: Liefert den vollständigen Recherche-Kontext

### Prompts
- `research_query`: Erzeugt einen Research-Query-Prompt

## Voraussetzungen

Bevor du den MCP-Server startest, stelle sicher, dass du Folgendes hast:

1. Python 3.10 oder neuer
2. API-Keys für die Dienste, die du nutzen möchtest:
   - OpenAI API Key
   - Tavily API Key oder andere Such-API-Keys

## Installation

1. GPT-Researcher-Repository klonen:
```bash
git clone https://github.com/assafelovic/gptr-mcp.git
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

3. Umgebungsvariablen einrichten:
   - `.env.example` zu `.env` kopieren:
   ```bash
   cp .env.example .env
   ```
   - `.env` bearbeiten und API-Keys eintragen:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## MCP-Server starten

Du kannst den Server auf zwei Arten starten:

### Methode 1: Direkt mit Python

```bash
python server.py
```

### Methode 2: Mit der MCP-CLI

```bash
mcp run server.py
```

Sobald der Server läuft, siehst du eine Meldung, dass er Verbindungen akzeptiert.

## Integration mit Claude

Es gibt zwei Hauptwege, den MCP-Server mit Claude zu verbinden:

1. **[API-Integration](./claude-integration)** - Programmatischer Zugriff über die Claude API
2. **[Desktop-Integration](./claude-desktop-integration)** - Nutzung mit der Claude-Desktop-App auf dem Mac

## Beispielnutzung mit Claude

```
User: Ich überlege, in NVIDIA zu investieren. Kannst du die aktuelle Lage des Unternehmens, die jüngste Kursentwicklung, Produktankündigungen und Analystenmeinungen recherchieren?

Claude: Ich helfe dir dabei, NVIDIA für Investitionszwecke zu recherchieren. Das dauert einen Moment, weil ich umfassend die aktuellsten Informationen zu Kursentwicklung, Entwicklungen und Experteneinschätzungen sammle.

[Claude nutzt das conduct_research-Tool - das dauert 30-40 Sekunden]

Claude: Auf Basis meiner Recherche hier eine umfassende Analyse des aktuellen Standes von NVIDIA:

## Aktueller Status von NVIDIA (NVDA)

### Jüngste Kursentwicklung
- Aktueller Kurs: $942.89 (zum Zeitpunkt der Recherche)
- YTD-Performance: +90.4%
- 52-Wochen-Spanne: $460.30 - $974.00
- Marktkapitalisierung: ca. $2.32 Billionen

### Wichtige jüngste Entwicklungen
1. **Blackwell-AI-Plattform**: Auf der GTC 2024 stellte NVIDIA die Blackwell-Architektur vor, die nächste Generation ihrer KI-Chip-Plattform, mit angeblich 4x mehr Leistung als Hopper.

2. **Q1 FY2025-Ergebnisse (Mai 2024)**:
   - R…
```
