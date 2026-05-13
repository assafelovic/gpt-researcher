# GPT Researcher

Das npm-Paket `gpt-researcher` ist ein WebSocket-Client für die Interaktion mit GPT Researcher.

<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted&?compact=true)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher ist ein offener Deep-Research-Agent für Web- und Lokalrecherche auf beliebige Aufgaben.**

Der Agent erzeugt detaillierte, faktenbasierte und möglichst neutrale Forschungsberichte mit Quellenangaben. GPT Researcher bietet umfangreiche Anpassungsmöglichkeiten, damit sich domänenspezifische Forschungsagenten bauen lassen. Inspiriert von den neueren [Plan-and-Solve](https://arxiv.org/abs/2305.04091)- und [RAG](https://arxiv.org/abs/2005.11401)-Arbeiten adressiert GPT Researcher Fehlinformationen, Geschwindigkeit, Determinismus und Zuverlässigkeit durch stabile Performance und parallelisierte Agentenarbeit.

**Unsere Mission ist es, Menschen und Organisationen mit präzisen, unvoreingenommenen und belastbaren Informationen durch KI zu unterstützen.**

## Installation

```bash
npm install gpt-researcher
```

## Verwendung

### Grundverwendung

```javascript
const GPTResearcher = require('gpt-researcher');

const researcher = new GPTResearcher({
  host: 'http://localhost:8000',
  logListener: (data) => console.log('logListener protokolliert Daten:', data)
});

researcher.sendMessage({
  query: 'Verringert besserer Kontext die Halluzinationen von LLMs?'
});
```

### Logdaten-Struktur

Die Funktion `logListener` erhält Protokolldaten in dieser Struktur:

```javascript
{
  type: 'logs',
  content: string,    // z. B. 'added_source_url', 'researching', 'scraping_content'
  output: string,     // Menschenlesbare Ausgabemeldung
  metadata: any       // Zusätzliche Daten (URLs, Zähler usw.)
}
```

Gängige `content`-Typen:

```javascript
'added_source_url': Neue Quell-URL hinzugefügt
'researching': Statusaktualisierung zur Recherche
'scraping_urls': URL-Scraping gestartet
'scraping_content': Fortschritt beim Inhaltsscraping
'scraping_images': Fortschritt bei der Bildverarbeitung
'scraping_complete': Scraping abgeschlossen
'fetching_query_content': Verarbeitung der Anfrage
```

### Parameter

- `task` (erforderlich): Die Forschungsfrage oder Aufgabe
- `reportType` (optional): Art des zu erzeugenden Berichts (Standard: `research_report`)
- `reportSource` (optional): Quelle der Berichtsdaten (Standard: `web`)
- `tone` (optional): Tonalität des Berichts
- `queryDomains` (optional): Liste von Domainnamen zur Filterung der Suchergebnisse

### Erweiterte Nutzung

```javascript
const researcher = new GPTResearcher({
  host: 'http://localhost:8000',
  logListener: (data) => console.log('Protokoll:', data)
});

// Erweiterte Nutzung mit allen Parametern
researcher.sendMessage({
  task: "Was sind die neuesten Entwicklungen im Bereich KI?",
  reportType: "research_report",
  reportSource: "web",
  queryDomains: ["techcrunch.com", "wired.com"]
});
```
