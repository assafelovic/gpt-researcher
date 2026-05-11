---
sidebar_position: 2
---

# Erweiterte Nutzung

Der MCP-Server kann in erweiterten Setups mit mehreren Tools, benutzerdefinierten Prompts und lokalen wie cloudbasierten Quellen verwendet werden.

## Typische Erweiterungen

- Zusätzliche Recherche-Tools anbinden
- Eigene Prompt-Vorlagen nutzen
- Lokale Dokumente in MCP-Flows einbeziehen
- Das Reporting auf bestimmte Domänen oder Themen spezialisieren

## Tipps

- Nutze `quick_search` für schnelle Antworten
- Nutze `deep_research` für gründliche Analysen
- Nutze `write_report`, wenn du aus den Ergebnissen direkt ein Dokument erzeugen willst
- Prüfe `get_research_context`, wenn du den gesamten Kontext im Anschluss weiterverwenden möchtest

## Fehlerbehebung

- Wenn keine Antworten zurückkommen, prüfe die API-Keys und die MCP-Verbindung
- Wenn die Ausgabe zu groß wird, verwende `quick_search` statt `deep_research`
- Wenn Claude zu viele Quellen ignoriert, begrenze die Aufgabe mit einem klaren Prompt
