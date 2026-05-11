# Wie du es auswählst

GPT Researcher ist ein leistungsstarker autonomer Research-Agent, der deine Rechercheprozesse verbessert und verschlankt. Egal, ob du als Entwickler Recherche-Funktionen in dein Projekt integrieren möchtest oder als Endnutzer eine umfassende Lösung suchst: GPT Researcher bietet flexible Optionen für unterschiedliche Anforderungen.

Wir stellen uns eine Zukunft vor, in der KI-Agenten gemeinsam komplexe Aufgaben lösen und Recherche dabei ein zentraler Schritt ist. GPT Researcher soll dein Standard-Agent für jede Recherchetätigkeit sein, unabhängig von der Komplexität. Er lässt sich leicht in bestehende Agenten-Workflows integrieren, sodass du keinen eigenen Research-Agenten von Grund auf bauen musst.

## Optionen

GPT Researcher bietet mehrere Möglichkeiten, seine Fähigkeiten zu nutzen:

<img src="https://github.com/user-attachments/assets/305fa3b9-60fa-42b6-a4b0-84740ab6c665" alt="Logo" width="568"></img>
<br></br>

1. **GPT Researcher PIP-Agent**: Ideal, um GPT Researcher in bestehende Projekte und Workflows einzubinden.
2. **Backend**: Ein Backend-Dienst zur Anbindung an die Frontend-Oberflächen mit erweiterten Funktionen wie detaillierten Reports.
3. **Multi-Agent-System**: Ein fortgeschrittenes Setup auf Basis von LangGraph mit den umfangreichsten Research-Funktionen.
4. **Frontend**: Verschiedene Frontend-Optionen je nach Bedarf, darunter eine einfache HTML/JS-Version und eine modernere NextJS-Version.

## Einsatzmöglichkeiten

### 1. PIP Package

Das PIP-Paket eignet sich ideal, wenn du GPT Researcher als Agent in deiner bevorzugten Entwicklungsumgebung und in deinem Code einsetzen willst.

**Vorteile:**
- Einfache Integration in bestehende Projekte
- Flexible Nutzung in Multi-Agent-Systemen, Chains oder Workflows
- Auf Produktionsleistung optimiert

**Nachteile:**
- Erfordert etwas Programmierwissen
- Für erweiterte Funktionen kann zusätzliche Einrichtung nötig sein

**Installation:**
```
pip install gpt-researcher
```

**Systemvoraussetzungen:**
- Python 3.10+
- Paketmanager `pip`

**Mehr erfahren:** [PIP-Dokumentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

### 2. End-to-End Application

Für ein komplettes Out-of-the-box-Erlebnis inklusive eines schicken Frontends kannst du unser Repository klonen.

**Vorteile:**
- Direkt nutzbare Frontend- und Backend-Dienste
- Enthält erweiterte Anwendungsfälle wie detaillierte Report-Erzeugung
- Optimale Nutzererfahrung

**Nachteile:**
- Weniger flexibel als das PIP-Paket für eigene Integrationen
- Das komplette Projekt muss eingerichtet werden

**Los geht's:**
1. Repository klonen: `git clone https://github.com/assafelovic/gpt-researcher.git`
2. Den [Installationsanweisungen](https://docs.gptr.dev/docs/gpt-researcher/getting-started) folgen

**Systemvoraussetzungen:**
- Git
- Python 3.10+
- Node.js und npm für das Frontend

**Beispiel für erweiterte Nutzung:** [Implementierung für detaillierte Reports](https://github.com/assafelovic/gpt-researcher/tree/master/backend/report_type/detailed_report)

### 3. Multi Agent System with LangGraph or AG2

Wir haben mit LangChain und AG2 zusammengearbeitet, um Multi-Agent-Workflows mit GPT Researcher zu unterstützen. Das ist die komplexeste und umfassendste Version von GPT Researcher.

**Vorteile:**
- Sehr detaillierte, maßgeschneiderte Research-Reports
- Interne Agenten-Schleifen und Reasoning

**Nachteile:**
- Teurer und zeitaufwendiger
- Für den Produktionseinsatz recht schwergewichtig

Diese Variante wird für lokale, experimentelle und didaktische Nutzung empfohlen. Wir arbeiten daran, bald eine schlankere Version bereitzustellen.

**Systemvoraussetzungen:**
- Python 3.10+
- LangGraph- oder AG2-Bibliothek

**Mehr erfahren:**
- [GPT Researcher x LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)
- [GPT Researcher x AG2](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2)

## Vergleichstabelle

| Funktion | PIP-Paket | End-to-End-Anwendung | Multi-Agent-System |
|---------|-------------|------------------------|---------------------|
| Integrationsaufwand | Hoch | Mittel | Niedrig |
| Anpassbarkeit | Hoch | Mittel | Hoch |
| UI direkt nutzbar | Nein | Ja | Nein |
| Komplexität | Niedrig | Mittel | Hoch |
| Am besten geeignet für | Entwickler | Endnutzer | Forschende/Experimentierende |

Hinweis: Alle Optionen wurden für den Produktionseinsatz optimiert und verfeinert.

## Tieferer Einblick

Wenn du mehr über die einzelnen Optionen erfahren möchtest, schau dir diese Dokus und Code-Snippets an:

1. **PIP-Paket**:
   - Install: `pip install gpt-researcher`
   - [Integrationsanleitung](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

2. **End-to-End-Anwendung**:
   - Clone the repository: `git clone https://github.com/assafelovic/gpt-researcher.git`
   - [Installationsanweisungen](https://docs.gptr.dev/docs/gpt-researcher/getting-started)

3. **Multi-Agent-System**:
   - [Multi-Agent-Code](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents)
   - [LangGraph-Dokumentation](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)
   - [AG2-Dokumentation](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2)
   - [Blog](https://docs.gptr.dev/blog/gptr-langgraph)

## Versionierung und Updates

GPT Researcher wird aktiv gepflegt und weiterentwickelt. Damit du die neueste Version nutzt:

- Für das PIP-Paket: `pip install --upgrade gpt-researcher`
- Für die End-to-End-Anwendung: Ziehe die neuesten Änderungen aus dem GitHub-Repository
- Für das Multi-Agent-System: Prüfe die Dokumentation auf Kompatibilität mit den aktuellen LangGraph- und AG2-Versionen

## Fehlerbehebung und FAQ

Bei häufigen Problemen und Fragen hilft dir unser [FAQ-Bereich](https://docs.gptr.dev/docs/faq) in der Dokumentation weiter.
