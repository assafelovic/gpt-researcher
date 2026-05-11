# Suchmaschinen

Suchmaschinen werden verwendet, um die relevantesten Webquellen und Inhalte für eine Research-Aufgabe zu finden. Du kannst deine bevorzugte Websuche auswählen oder einen eigenen Retriever einsetzen.

## Web-Suchmaschinen

GPT Researcher verwendet standardmäßig [DuckDuckGo](https://pypi.org/project/duckduckgo-search/), wenn kein Tavily-Key konfiguriert ist.
Du kannst auch andere Suchmaschinen über die Umgebungsvariable `RETRIEVER` angeben. Beachte, dass jede Suchmaschine ihre eigenen API-Keys und Nutzungslimits hat.

Beispiel:

```bash
RETRIEVER=bing
```

Du kannst auch mehrere Retriever angeben, indem du sie mit Kommas trennst. Das System nutzt sie dann nacheinander.

```bash
RETRIEVER=duckduckgo, arxiv
```

Dank unserer Community sind diese Web-Suchmaschinen integriert:

- [Tavily](https://app.tavily.com) - optional, benötigt `TAVILY_API_KEY`
- [Bing](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) - `RETRIEVER=bing`
- [Google](https://developers.google.com/custom-search/v1/overview) - `RETRIEVER=google`
- [SearchApi](https://www.searchapi.io/) - `RETRIEVER=searchapi`
- [Serp API](https://serpapi.com/) - `RETRIEVER=serpapi`
- [Serper](https://serper.dev/) - `RETRIEVER=serper`
- [Searx](https://searx.github.io/searx/) - `RETRIEVER=searx`
- [DuckDuckGo](https://pypi.org/project/duckduckgo-search/) - Standard, wenn kein Tavily-Key gesetzt ist
- [Arxiv](https://info.arxiv.org/help/api/index.html) - `RETRIEVER=arxiv`
- [Exa](https://docs.exa.ai/reference/getting-started) - `RETRIEVER=exa`
- [PubMedCentral](https://www.ncbi.nlm.nih.gov/home/develop/api/) - `RETRIEVER=pubmed_central`

## Eigene Retriever

Du kannst auch einen eigenen Retriever verwenden, indem du `RETRIEVER=custom` setzt.
Damit kannst du jede Suchmaschine nutzen, die über eine API Dokumente zurückliefert. Das ist vor allem für Enterprise-Use-Cases praktisch.

Zusätzlich zu `RETRIEVER` brauchst du diese Variablen:

- `RETRIEVER_ENDPOINT`: Die URL deines benutzerdefinierten Retrievers
- Weitere benötigte Argumente im Format `RETRIEVER_ARG_...`, zum Beispiel `RETRIEVER_ARG_API_KEY`

### Beispiel

```bash
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://api.myretriever.com
RETRIEVER_ARG_API_KEY=YOUR_API_KEY
```

### Antwortformat

Damit der Custom Retriever korrekt funktioniert, muss die Antwort im folgenden Format zurückkommen:

```json
[
  {
    "url": "http://example.com/page1",
    "raw_content": "Content of page 1"
  },
  {
    "url": "http://example.com/page2",
    "raw_content": "Content of page 2"
  }
]
```

Das System erwartet genau dieses Format und verarbeitet die Quellenliste entsprechend.

## Suchmaschinen-Konfiguration

### Serper

Um [Serper](https://serper.dev/) zu verwenden:

1. API-Key auf [serper.dev](https://serper.dev/) holen
2. Die Umgebungsvariablen setzen:

```bash
RETRIEVER=serper
SERPER_API_KEY=your_api_key_here
```

**Optionale Konfiguration:**

```bash
SERPER_REGION=us                    # Ländercode (us, kr, jp, etc.)
SERPER_LANGUAGE=en                  # Sprachcode (en, ko, ja, etc.)
SERPER_TIME_RANGE=qdr:w             # Zeitfilter (qdr:h, qdr:d, qdr:w, qdr:m, qdr:y)
SERPER_EXCLUDE_SITES=youtube.com    # Seiten ausschließen (durch Kommas getrennt)
```

Fehlt dir ein Retriever? Dann eröffne gern ein Issue oder einen Pull Request auf unserer [GitHub-Seite](https://github.com/assafelovic/gpt-researcher).
