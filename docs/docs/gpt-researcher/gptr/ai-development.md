---
sidebar_label: KI-gestützte Entwicklung
sidebar_position: 6
---

# 🤖 KI-gestützte Entwicklung mit Claude

GPT Researcher enthält eine umfassende Skill-Datei, mit der KI-Assistenten wie Claude den Codebestand besser verstehen, nutzen und erweitern können. Dieser Leitfaden zeigt, wie du Claude Code zum Beitragen an GPT Researcher einsetzen kannst.

## Überblick

Wir pflegen ein `.claude/skills/`-Verzeichnis mit ausführlicher Dokumentation, die Claude automatisch erkennt und beim Arbeiten mit diesem Repository nutzt. Das ermöglicht:

- **Schnelleres Onboarding** - Claude versteht die Architektur sofort
- **Konsistente Beiträge** - Eingeführte Muster werden beibehalten
- **Weniger Fehler** - Häufige Stolperfallen und Best Practices sind bekannt
- **Ende-zu-Ende-Funktionen** - Claude kann komplette Funktionen nach dem 8-Schritte-Muster umsetzen

## Das Skills-Verzeichnis

```
.claude/
└── skills/
    ├── SKILL.md      # Umfassender Entwicklungsleitfaden (~1.500 Zeilen)
    └── REFERENCE.md  # Schnelle Referenz für Config, API, WebSocket-Events
```

### Was in `SKILL.md` steckt

| Abschnitt | Beschreibung |
|---------|-------------|
| Architektur-Deep-Dive | Vollständiges Systemdiagramm mit allen Schichten und Komponenten |
| Kernkomponenten | Methodensignaturen für `GPTResearcher`, `ResearchConductor` usw. |
| End-to-End-Flow | Vollständige Codepfade von der Anfrage bis zum Report |
| Datenfluss | Was zwischen den Komponenten übergeben wird |
| Prompt-System | Reale Prompt-Beispiele aus `prompts.py` |
| Retriever-System | Alle 14 Retriever, inklusive Anleitung zum Hinzufügen neuer Retriever |
| MCP-Integration | Strategieoptionen, Konfiguration, Verarbeitungslogik |
| Deep Research | Konfiguration rekursiver Erkundung |
| Multi-Agent-System | LangGraph-basierter 8-Agenten-Workflow |
| Fallstudie Bildgenerierung | Vollständige echte Implementierung als Referenz |
| 8-Schritte-Funktionsmuster | So fügst du neue Funktionen hinzu |
| Erweiterte Nutzung | Callbacks, LangChain, Vector Stores |
| Fehlerbehandlung | Muster für sanfte Degradierung |
| Testleitfaden | pytest-Setup und Beispiele |
| Wichtige Stolperfallen | Häufige Fehler, die du vermeiden solltest |

### Was in `REFERENCE.md` steckt

- Alle Umgebungsvariablen
- REST-API-Endpunkte
- WebSocket-Nachrichtentypen
- Parameter des Python-Clients

## Claude Code verwenden

### Installation

1. [Claude Code](https://claude.ai/code) installieren, als VS-Code-Extension oder CLI
2. Das GPT-Researcher-Repository öffnen
3. Claude entdeckt die Skills in `.claude/skills/` automatisch

### Beispiel-Prompts

**Codebasis verstehen:**
```
Wie funktioniert der Research-Flow von der Anfrage bis zum Report?
```

**Eine Funktion hinzufügen:**
```
Ich möchte eine Funktion hinzufügen, die Audio-Zusammenfassungen von Reports erstellt.
Nutze dabei das 8-Schritte-Muster aus der Skill-Datei.
```

**Debugging:**
```
Warum werden Bilder möglicherweise nicht im Report angezeigt? Prüfe den Bildgenerierungs-Flow.
```

**Funktionalität erweitern:**
```
Füge einen neuen Retriever für Wikipedia hinzu. Halte dich dabei an das Retriever-Muster in den Skills.
```

### Was Claude kann

Mit geladenen Skills kann Claude:

1. **Jeden Teil der Codebasis erklären** - Architektur, Datenfluss, Komponenteninteraktionen
2. **Funktionen Ende-zu-Ende implementieren** - Config → Provider → Skill → Agent → Prompts → Frontend
3. **Probleme debuggen** - Versteht häufige Stolperfallen und Fehlermuster
4. **Tests schreiben** - Kennt Testmuster und pytest-Setup
5. **Retriever hinzufügen** - Folgt exakt dem Muster für neue Suchmaschinen
6. **Prompts anpassen** - Versteht das PromptFamily-System
7. **Die API erweitern** - Kennt FastAPI-Muster und WebSocket-Events

## Mit Claude beitragen

### Vor dem Start

1. Repository forken und klonen
2. In editierbarem Modus installieren: `pip install -e .`
3. `.env`-Datei mit den nötigen API-Keys einrichten
4. Das Projekt in einem Editor mit Claude Code öffnen

### Beitrags-Workflow

1. **Feature/Fix beschreiben** und Claude den Kontext geben
2. **Claude implementieren lassen** und dabei die bestehenden Muster befolgen
3. **Änderungen prüfen** - Claude erklärt, was geändert wurde
4. **Gründlich testen** - `python -m pytest tests/`
5. **PR einreichen** mit klarer Beschreibung

### Beispiel: Eine neue Funktion hinzufügen

```
Ich möchte eine Funktion hinzufügen, mit der Nutzer einen eigenen
Schreibstil für Reports angeben können, z. B. "akademisch", "Blogpost" oder "Executive Summary".

Das soll:
1. über eine Umgebungsvariable konfigurierbar sein
2. den Report-Generierungs-Prompt beeinflussen
3. optional sein und einen sinnvollen Standard haben

Bitte setze das nach dem 8-Schritte-Muster um.
```

Claude würde dann:
1. `REPORT_STYLE` zu den Konfigurations-Defaults hinzufügen
2. Den Typ zu `BaseConfig` ergänzen
3. Den Prompt in `prompts.py` aktualisieren
4. Genau zeigen, was geändert wurde
5. Auf mögliche Stolperfallen hinweisen, etwa Kleinbuchstaben-Zugriffe auf Config-Werte

## Skills aktualisieren

Wenn du größere Funktionen hinzufügst oder die Architektur änderst:

1. Aktualisiere `.claude/skills/SKILL.md` mit den neuen Mustern
2. Füge neue Config-Variablen zu `.claude/skills/REFERENCE.md` hinzu
3. Nimm deine Funktion als Fallstudie auf, wenn sie ein gutes Beispiel ist

### Best Practices für Skill-Dateien

- Verwende echte Codebeispiele aus der Umsetzung
- Beschreibe immer sowohl das „Was“ als auch das „Warum“
- Dokumentiere Stolperfallen deutlich
- Aktualisiere Datenflussdiagramme, wenn Komponenten hinzukommen
- Ergänze neue Funktionen in den Abschnitten zu den unterstützten Optionen

## Warum das wichtig ist

KI-gestützte Entwicklung wird immer mehr zum Standard. Hochwertige Skill-Dateien bringen Vorteile:

- **Neue Contributor** können sich in Minuten statt Stunden einarbeiten
- **Erfahrene Contributor** arbeiten mit KI-Unterstützung schneller
- **Die Codequalität** bleibt über Beiträge hinweg konsistent
- **Die Dokumentation** bleibt als Nebeneffekt aktuell

Die Skill-Datei ist im Grunde ein „Brain Dump“ von allem, was ein erfahrener Entwickler über GPT Researcher wissen muss - verfügbar für KI-Assistenten.

## Mehr erfahren

- [Claude Code Dokumentation](https://claude.ai/code/docs)
- [Anthropic Agent Skills](https://github.com/anthropics/skills)
- [Beitragsrichtlinien](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md)
