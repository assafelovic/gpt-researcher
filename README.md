<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord](https://img.shields.io/discord/1127851779011391548?logo=discord&logoColor=white&label=Discord&color=34b76a&style=for-the-badge)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Skill](https://img.shields.io/badge/Claude%20Skill-skills.sh-blueviolet?style=flat&logo=anthropic&logoColor=white)](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher ist ein offener Deep-Research-Agent für Web- und Lokalrecherche auf beliebige Aufgaben.**

Der Agent erzeugt detaillierte, faktenbasierte und möglichst neutrale Forschungsberichte mit Quellenangaben. GPT Researcher bietet umfangreiche Anpassungsmöglichkeiten, damit sich domänenspezifische Forschungsagenten bauen lassen. Inspiriert von den neueren [Plan-and-Solve](https://arxiv.org/abs/2305.04091)- und [RAG](https://arxiv.org/abs/2005.11401)-Arbeiten adressiert GPT Researcher Fehlinformationen, Geschwindigkeit, Determinismus und Zuverlässigkeit durch stabile Performance und parallelisierte Agentenarbeit.

**Unsere Mission ist es, Menschen und Organisationen mit präzisen, unvoreingenommenen und belastbaren Informationen durch KI zu unterstützen.**

## Warum GPT Researcher?

- Objektive Schlussfolgerungen aus manueller Recherche können Wochen dauern und verschlingen enorme Ressourcen.
- Auf veralteten Informationen trainierte LLMs halluzinieren und werden für aktuelle Recherchen schnell unbrauchbar.
- Viele LLMs haben Token-Limits, die für lange Forschungsberichte nicht ausreichen.
- Begrenzte Webquellen in bestehenden Diensten führen zu Fehlinformationen und oberflächlichen Ergebnissen.
- Selektive Webquellen können Forschungsergebnisse verzerren.

## Demo
<a href="https://www.youtube.com/watch?v=f60rlc_QCxE" target="_blank" rel="noopener">
  <img src="https://github.com/user-attachments/assets/ac2ec55f-b487-4b3f-ae6f-b8743ad296e4" alt="Demo-Video" width="800" target="_blank" />
</a>

## Als Claude-Skill installieren

Erweitere die Deep-Research-Fähigkeiten von Claude, indem du GPT Researcher als [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher) installierst:

```bash
npx skills add assafelovic/gpt-researcher
```

Nach der Installation kann Claude die Deep-Research-Funktionen von GPT Researcher direkt in Gesprächen verwenden.

## Fork-spezifischer lokaler Stack

Dieser Repository-Snapshot wurde mit einem lokalen Gemma-/llama.cpp-Server und einem angepassten Backend-/Frontend-Stack validiert.

- LLM-Server: `http://127.0.0.1:8081`
- Backend-API: `http://127.0.0.1:8002`
- Frontend: `http://127.0.0.1:3000`
- Forschungsartefakte: `outputs/`

Siehe die fork-spezifischen Hinweise in [docs/docs/gpt-researcher/gptr/local-stack.md](docs/docs/gpt-researcher/gptr/local-stack.md).

Strukturierte LLM-Ausgaben werden im Backend über einen gemeinsamen JSON-Parser normalisiert. Dadurch bleiben Planner-, Critic-, Tool-Selection- und Bildgenerator-Flows auch dann stabil, wenn ein Modell versehentlich Code-Fences oder leicht beschädigte JSON-Payloads liefert. Die Prompts bleiben trotzdem auf reines JSON ausgerichtet.

## Architektur

Die Kernidee ist die Nutzung von „Planer“- und „Ausführungs“-Agenten. Der Planer erzeugt Forschungsfragen, während die Ausführungsagenten relevante Informationen sammeln. Der Publisher fasst anschließend alle Ergebnisse in einem umfassenden Bericht zusammen.

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>

Schritte:
* Erzeuge einen auf die Aufgabe zugeschnittenen Agenten auf Basis einer Forschungsfrage.
* Entwickle Fragen, die gemeinsam eine objektive Einschätzung der Aufgabe ergeben.
* Nutze einen Crawler-Agenten, um Informationen zu jeder Frage zu sammeln.
* Fasse jede Quelle zusammen und verfolge ihre Herkunft.
* Filtere und aggregiere die Zusammenfassungen zu einem finalen Forschungsbericht.

## Anleitungen
 - [So funktioniert es](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [So installierst du es](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live-Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## Funktionen

- 📝 Erstelle detaillierte Forschungsberichte auf Basis von Web- und lokalen Dokumenten.
- 🖼️ Intelligentes Bild-Scraping und Filtern für Berichte.
- 🍌 **KI-generierte Inline-Bilder** mit Google Gemini (Nano Banana) für visuelle Illustrationen.
- 📜 Erzeuge ausführliche Berichte mit mehr als 2.000 Wörtern.
- 🌐 Aggregiere über 20 Quellen für objektive Schlussfolgerungen.
- 🖥️ Frontend als leichtgewichtige Variante (HTML/CSS/JS) und als produktionsreife Variante (NextJS + Tailwind) verfügbar.
- 🔍 Web-Scraping mit JavaScript-Unterstützung.
- 📂 Behält während der Recherche Gedächtnis und Kontext.
- 📄 Exportiere Berichte als PDF, Word und in weitere Formate.

## 📖 Dokumentation

Siehe die [Dokumentation](https://docs.gptr.dev/docs/gpt-researcher/getting-started) für:
- Installations- und Einrichtungsanleitungen
- Konfigurations- und Anpassungsoptionen
- How-to-Beispiele
- Vollständige API-Referenzen

## ⚙️ Erste Schritte

### Installation

1. Installiere Python 3.11 oder neuer. [Anleitung](https://www.tutorialsteacher.com/python/install-python).
2. Klone das Projekt und wechsle in das Verzeichnis:

    ```bash
    git clone https://github.com/assafelovic/gpt-researcher.git
    cd gpt-researcher
    ```

3. Lege API-Schlüssel per Umgebungsvariablen oder in einer `.env`-Datei ab.

    ```bash
    export OPENAI_API_KEY={Dein OpenAI-API-Schlüssel}
    # Optional: konfiguriere einen Web-Retriever, wenn du DuckDuckGo überschreiben willst.
    # export TAVILY_API_KEY={Dein Tavily-API-Schlüssel}
    ```

    Standardmäßig nutzt die Websuche DuckDuckGo. Setze einen Retriever-API-Schlüssel nur dann, wenn du den Standard mit Tavily oder einem anderen Anbieter überschreiben willst.

    (Optional) Für erweitertes Tracing und Observability kannst du außerdem setzen:
    
    ```bash
    # export LANGCHAIN_TRACING_V2=true
    # export LANGCHAIN_API_KEY={Dein LangChain-API-Schlüssel}
    ```

    Für benutzerdefinierte OpenAI-kompatible APIs (z. B. lokale Modelle oder andere Anbieter) kannst du außerdem setzen:
    
    ```bash
    export OPENAI_BASE_URL={Deine benutzerdefinierte API-Basis-URL}
    ```

4. Installiere die Abhängigkeiten und starte den Server:

    ```bash
    pip install -r requirements.txt
    python -m uvicorn main:app --reload
    ```

Rufe [http://localhost:8000](http://localhost:8000) auf, um zu starten.

Für andere Setups (z. B. Poetry oder virtuelle Umgebungen) sieh dir die [Getting-Started-Seite](https://docs.gptr.dev/docs/gpt-researcher/getting-started) an.

## Als PIP-Paket ausführen
```bash
pip install gpt-researcher

```
### Beispielverwendung:
```python
...
from gpt_researcher import GPTResearcher

query = "why is Nvidia stock going up?"
researcher = GPTResearcher(query=query)
# Starte die Recherche für die angegebene Frage
research_result = await researcher.conduct_research()
# Schreibe den Bericht
report = await researcher.write_report()
...
```

**Weitere Beispiele und Konfigurationen findest du auf der [PIP-Dokumentationsseite](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package).**

### 🔧 MCP-Client
GPT Researcher unterstützt MCP-Integration, um mit spezialisierten Datenquellen wie GitHub-Repositories, Datenbanken und benutzerdefinierten APIs zu verbinden. Damit kann Recherche auf Datenquellen zusätzlich zur Websuche erfolgen.

```bash
export RETRIEVER=duckduckgo,mcp  # Hybridrecherche aus Web + MCP aktivieren
```

```python
from gpt_researcher import GPTResearcher
import asyncio
import os

async def mcp_research_example():
    # MCP zusammen mit Websuche aktivieren
    os.environ["RETRIEVER"] = "duckduckgo,mcp"
    
    researcher = GPTResearcher(
        query="What are the top open source web research agents?",
        mcp_configs=[
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
            }
        ]
    )
    
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report
```

> Eine umfassende MCP-Dokumentation und erweiterte Beispiele findest du im [MCP-Integrationsleitfaden](https://docs.gptr.dev/docs/gpt-researcher/retrievers/mcp-configs).

## 🍌 Inline-Bildgenerierung

GPT Researcher kann automatisch KI-erzeugte Illustrationen in Forschungsberichte einbetten, indem Google-Gemini-Modelle (Nano Banana) verwendet werden.

```bash
# In deiner .env-Datei aktivieren
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=your_google_api_key
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
```

Wenn die Funktion aktiviert ist, passiert Folgendes:
1. Der Forschungskontext wird analysiert, um Visualisierungsmöglichkeiten zu erkennen
2. Während der Recherchephase werden 2 bis 3 passende Bilder vorab erzeugt
3. Die Bilder werden direkt beim Schreiben des Berichts eingebettet

Die Bilder werden im Dark-Mode-Stil erzeugt, der zur GPT-Researcher-UI passt, mit professioneller Infografik-Ästhetik und türkisfarbenen Akzenten.

[Mehr über die Bildgenerierung erfahren](https://docs.gptr.dev/docs/gpt-researcher/gptr/image_generation) in unserer Dokumentation.

## ✨ Deep Research

GPT Researcher enthält jetzt Deep Research - einen fortgeschrittenen rekursiven Forschungs-Workflow, der Themen mit Tiefe und Breite erkundet. Diese Funktion verwendet ein baumartiges Erkundungsmuster und taucht tiefer in Unterthemen ein, während sie gleichzeitig einen Gesamtüberblick über das Thema behält.

- 🌳 Baumartige Erkundung mit konfigurierbarer Tiefe und Breite
- ⚡️ Parallele Verarbeitung für schnellere Ergebnisse
- 🤝 Intelligentes Kontextmanagement über Forschungszweige hinweg
- ⏱️ Etwa 5 Minuten pro Deep-Research-Lauf
- 💰 Etwa 0,4 $ pro Recherche (mit `o3-mini` bei Reasoning-Effort „high“)

[Mehr über Deep Research erfahren](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research) in unserer Dokumentation.

## Mit Docker ausführen

> **Schritt 1** - [Docker installieren](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **Schritt 2** - Die Datei `.env.example` kopieren, deine API-Schlüssel in die Kopie eintragen und die Datei als `.env` speichern.

> **Schritt 3** - In der `docker-compose`-Datei die Dienste auskommentieren, die du nicht mit Docker ausführen willst.

```bash
docker-compose up --build
```

Wenn das nicht funktioniert, probiere es ohne Bindestrich:
```bash
docker compose up --build
```

> **Schritt 4** - Standardmäßig startet dieser Ablauf, sofern du in deiner `docker-compose`-Datei nichts auskommentiert hast, zwei Prozesse:
 - den Python-Server auf `localhost:8000`<br>
 - die React-App auf `localhost:3000`<br>

Rufe `localhost:3000` im Browser auf und lege direkt los.


## 📄 Recherche auf lokalen Dokumenten

Du kannst GPT Researcher anweisen, Aufgaben auf Basis lokaler Dokumente zu bearbeiten. Unterstützte Dateiformate sind derzeit: PDF, Klartext, CSV, Excel, Markdown, PowerPoint und Word-Dokumente.

Schritt 1: Lege die Umgebungsvariable `DOC_PATH` an, die auf den Ordner mit deinen Dokumenten zeigt.

```bash
export DOC_PATH="./my-docs"
```

Schritt 2:
 - Wenn du die Frontend-App auf `localhost:8000` ausführst, wähle einfach „My Documents“ in der Dropdown-Option „Report Source“ aus.
- Wenn du GPT Researcher mit dem [PIP-Paket](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package) verwendest, übergib das Argument `report_source` als `"local"`, wenn du die Klasse `GPTResearcher` instanziierst. Ein Codebeispiel findest du [hier](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research).


## 🤖 MCP-Server

Unser MCP-Server wurde in ein eigenes Repository verschoben: [gptr-mcp](https://github.com/assafelovic/gptr-mcp).

Der GPT Researcher MCP-Server ermöglicht es KI-Anwendungen wie Claude, tiefergehende Recherchen durchzuführen. Während LLM-Apps mit MCP Websuche-Tools nutzen können, liefert der GPT Researcher MCP tiefere und zuverlässigere Forschungsergebnisse.

Funktionen:
- Deep-Research-Fähigkeiten für KI-Assistenten
- Höhere Informationsqualität durch optimierte Kontextnutzung
- Umfassende Ergebnisse mit besserem Reasoning für LLMs
- Claude-Desktop-Integration

Ausführliche Installations- und Nutzungshinweise findest du im [offiziellen Repository](https://github.com/assafelovic/gptr-mcp).


## 👪 Multi-Agent-Assistent
Während sich KI von Prompt Engineering und RAG hin zu Multi-Agent-Systemen entwickelt, freuen wir uns, Multi-Agent-Assistenten auf Basis von [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) und [AG2](https://github.com/ag2ai/ag2) vorzustellen.

Durch den Einsatz von Multi-Agent-Frameworks kann der Forschungsprozess in Tiefe und Qualität deutlich verbessert werden, indem mehrere spezialisierte Agenten zusammenarbeiten. Inspiriert von der jüngeren [STORM](https://arxiv.org/abs/2402.14207)-Arbeit zeigt dieses Projekt, wie ein Team von KI-Agenten gemeinsam eine Recherche von der Planung bis zur Veröffentlichung durchführen kann.

Ein durchschnittlicher Lauf erzeugt einen 5- bis 6-seitigen Forschungsbericht in mehreren Formaten wie PDF, Docx und Markdown.

Sieh es dir [hier](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents) an oder besuche unsere Dokumentation zu [LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) und [AG2](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2) für weitere Informationen.

## 🔍 Observability

GPT Researcher unterstützt **LangSmith** für erweitertes Tracing und Observability, damit sich komplexe Multi-Agent-Workflows leichter debuggen und optimieren lassen.

So aktivierst du Tracing:
1. Setze die folgenden Umgebungsvariablen:
   ```bash
   export LANGCHAIN_TRACING_V2=true
   export LANGCHAIN_API_KEY=your_api_key
   export LANGCHAIN_PROJECT="gpt-researcher"
   ```
2. Starte deine Rechercheaufgaben wie gewohnt. Alle LangGraph-basierten Agenteninteraktionen werden automatisch getraced und in deinem LangSmith-Dashboard visualisiert.

## 🖥️ Frontend-Anwendungen

GPT-Researcher verfügt jetzt über ein verbessertes Frontend, das die Benutzererfahrung verbessert und den Forschungsprozess strafft. Das Frontend bietet:

- Eine intuitive Oberfläche für Forschungsanfragen
- Echtzeit-Fortschrittsanzeige für laufende Aufgaben
- Interaktive Darstellung von Forschungsergebnissen
- Anpassbare Einstellungen für maßgeschneiderte Rechercheerlebnisse

Es stehen zwei Bereitstellungsoptionen zur Verfügung:
1. Ein leichtgewichtiges statisches Frontend, das über FastAPI ausgeliefert wird
2. Eine funktionsreiche NextJS-Anwendung für erweiterte Funktionen

Für detaillierte Einrichtungsanleitungen und weitere Informationen zu den Frontend-Funktionen besuche bitte unsere [Dokumentationsseite](https://docs.gptr.dev/docs/gpt-researcher/frontend/introduction).

## 🚀 Mitwirken
Beiträge sind sehr willkommen! Schau dir bitte [contributing](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md) an, wenn du mitmachen möchtest.

Sieh dir bitte auch unsere [Roadmap](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) an und melde dich über unsere [Discord-Community](https://discord.gg/QgZXvJAccX), wenn du bei unserer Mission mitmachen möchtest.
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher&max=1000" />
</a>
## ✉️ Support / Kontakt
- [Community Discord](https://discord.gg/spBgZmm3Xe)
- E-Mail des Autors: assaf.elovic@gmail.com

## 🛡 Haftungsausschluss

Dieses Projekt, GPT Researcher, ist eine experimentelle Anwendung und wird „wie besehen“ ohne jegliche ausdrückliche oder stillschweigende Gewährleistung bereitgestellt. Wir stellen den Code zu akademischen Zwecken unter der Apache-2-Lizenz bereit. Nichts hierin ist akademische Beratung und keine Empfehlung, es in akademischen Arbeiten oder Forschungsarbeiten zu verwenden.

Unsere Sicht auf unvoreingenommene Forschungsaussagen:
1. Das Hauptziel von GPT Researcher ist es, falsche und verzerrte Fakten zu reduzieren. Wie? Wir nehmen an, dass die Wahrscheinlichkeit für falsche Daten sinkt, je mehr Seiten wir scrapen. Wenn wir für eine Recherche mehrere Seiten scrapen und die häufigsten Informationen auswählen, ist die Chance, dass sie alle falsch sind, extrem gering.
2. Wir wollen Verzerrungen nicht vollständig eliminieren; wir wollen sie so weit wie möglich reduzieren. **Wir sind hier als Community, um die wirksamsten Interaktionen zwischen Mensch und LLM herauszufinden.**
3. Auch Menschen neigen in der Forschung zu Verzerrungen, da viele bereits Meinungen zu den Themen haben, über die sie recherchieren. Dieses Tool scrapt viele Meinungen und erklärt unterschiedliche Sichtweisen gleichgewichtig, die eine voreingenommene Person sonst nie gelesen hätte.

---

<p align="center">
<a href="https://star-history.com/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>

<p align="right">
  <a href="#top">⬆️ Zurück nach oben</a>
</p>
