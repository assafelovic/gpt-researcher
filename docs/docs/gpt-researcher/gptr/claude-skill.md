# Claude Skill

GPT Researcher ist als [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher) verfügbar. Damit kannst du Claudes Recherche-Fähigkeiten direkt in Claude Code und anderen Claude-gestützten Anwendungen erweitern.

## Was sind Claude Skills?

Skills sind modulare Pakete, die Claudes Fähigkeiten durch spezialisiertes Wissen, Workflows und Werkzeuge erweitern. Wenn du GPT Researcher als Skill installierst, erhält Claude Zugriff auf tiefere Rechercheabläufe mit Zitaten.

## Installation

Installiere GPT Researcher als Claude Skill mit dem Skills-CLI:

```bash
npx skills add assafelovic/gpt-researcher
```

Dadurch wird der Skill aus dem [GPT-Researcher-GitHub-Repository](https://github.com/assafelovic/gpt-researcher) installiert.

## Was enthalten ist

Der GPT-Researcher-Skill gibt Claude Zugriff auf:

- **Architektur-Wissen** - Verständnis des Planner-Executor-Publisher-Musters
- **Komponenten-Signaturen** - Methodensignaturen für `GPTResearcher`, `ResearchConductor`, `ReportGenerator`
- **Integrationsmuster** - Wie man Features hinzufügt, Retriever erweitert und Workflows anpasst
- **Konfigurationsreferenz** - Alle Umgebungsvariablen und Config-Optionen
- **API-Referenz** - REST- und WebSocket-API-Dokumentation

## Nutzung

Nach der Installation kann Claude dir helfen bei:

- dem Verständnis der GPT-Researcher-Architektur
- dem Hinzufügen neuer Funktionen nach dem 8-Schritte-Muster
- dem Debuggen von Research-Pipelines
- der Integration von MCP-Datenquellen
- der Anpassung der Report-Erzeugung
- dem Hinzufügen neuer Retriever

## Struktur des Skills

Der Skill liegt im `.claude/`-Verzeichnis des Repos:

```
.claude/
├── SKILL.md              # Hauptdatei des Skills (schlank, <500 Zeilen)
└── references/           # Detaillierte Dokumentation
    ├── architecture.md
    ├── components.md
    ├── flows.md
    ├── prompts.md
    ├── retrievers.md
    ├── mcp.md
    ├── deep-research.md
    ├── multi-agents.md
    ├── adding-features.md
    ├── advanced-patterns.md
    ├── api-reference.md
    └── config-reference.md
```

## Mehr erfahren

- [Skills.sh - GPT Researcher](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher) - Anzeige im Skills.sh-Register
- [Claude Code Dokumentation](https://docs.claude.com/en/docs/claude-code/skills) - Offizielle Skills-Dokumentation
- [GPT-Researcher-Dokumentation](https://docs.gptr.dev) - Vollständige Projektdokumentation
