# Konfiguration

Mit `config.py` kannst du GPT Researcher an deine konkreten Anforderungen und Vorlieben anpassen.

Dank unserer großartigen Community unterstützt GPT Researcher mehrere LLMs und Retriever.
Außerdem lässt sich GPT Researcher auf verschiedene Report-Formate, Wortanzahl, Recherchetiefe und mehr abstimmen.

GPT Researcher nutzt standardmäßig unsere empfohlene Integrationskombination: [OpenAI](https://platform.openai.com/docs/overview) für LLM-Aufrufe und [DuckDuckGo](https://pypi.org/project/duckduckgo-search/) für Echtzeit-Webinfos, wenn kein Retriever-API-Key gesetzt ist. Tavily bleibt als optionaler Retriever verfügbar, sobald du `TAVILY_API_KEY` setzt.

Wie unten zu sehen ist, gilt OpenAI weiterhin als das stärkere LLM. Wir gehen davon aus, dass das vorerst so bleibt und dass Preise weiter sinken, während Performance und Geschwindigkeit steigen.

<div style={{ marginBottom: '10px' }}>
<img align="center" height="350" src="/img/leaderboard.png" />
</div>

Die Standarddatei `config.py` findest du unter `/gpt_researcher/config/`. Sie bietet verschiedene Optionen, um GPT Researcher an deine Anforderungen anzupassen.
Du kannst auch eine eigene externe JSON-Datei `config.json` einbinden, indem du den Pfad im Parameter `config_path` angibst.
Die JSON-Datei sollte dieselben Schlüssel und Formate wie die Standardkonfiguration verwenden. Hier ein Beispiel als Ausgangspunkt:
```json
{
  "RETRIEVER": "duckduckgo",
  "EMBEDDING": "openai:text-embedding-3-small",
  "SIMILARITY_THRESHOLD": 0.42,
  "FAST_LLM": "openai:gpt-4o-mini",
  "SMART_LLM": "openai:gpt-4.1",
  "STRATEGIC_LLM": "openai:o4-mini",
  "LANGUAGE": "german",
  "CURATE_SOURCES": false,
  "FAST_TOKEN_LIMIT": 2000,
  "SMART_TOKEN_LIMIT": 4000,
  "STRATEGIC_TOKEN_LIMIT": 4000,
  "BROWSE_CHUNK_MAX_LENGTH": 8192,
  "SUMMARY_TOKEN_LIMIT": 700,
  "TEMPERATURE": 0.4,
  "DOC_PATH": "./my-docs",
  "REPORT_SOURCE": "web"
}
```


Um GPT Researcher mit einer bestimmten Konfiguration zu starten, kannst du zum Beispiel Folgendes tun:
```bash
python gpt_researcher/main.py --config_path my_config.json
```




 **Für zukünftige Erweiterungen bitte auch die `config.py` beachten.**

Hier ist eine Liste der aktuell unterstützten Optionen:

- **`RETRIEVER`**: Web-Suchmaschine zum Abrufen von Quellen. Standard ist `duckduckgo`, wenn kein `TAVILY_API_KEY` gesetzt ist. Optionen: `duckduckgo`, `bing`, `google`, `searchapi`, `serper`, `searx`, `tavily`. [Hier](https://github.com/assafelovic/gpt-researcher/tree/master/gpt_researcher/retrievers) findest du die unterstützten Retriever.
- **`EMBEDDING`**: Embedding-Modell. Standard ist `openai:text-embedding-3-small`. Optionen: `ollama`, `huggingface`, `azure_openai`, `custom`.
- **`SIMILARITY_THRESHOLD`**: Schwellenwert für den Ähnlichkeitsvergleich beim Verarbeiten von Dokumenten. Standard: `0.42`.
- **`FAST_LLM`**: Modellname für schnelle LLM-Aufgaben wie Zusammenfassungen. Standard: `openai:gpt-4o-mini`.
- **`SMART_LLM`**: Modellname für intelligente Aufgaben wie Report-Erstellung und Reasoning. Standard: `openai:gpt-5`.
- **`STRATEGIC_LLM`**: Modellname für strategische Aufgaben wie Recherchepläne und Strategien. Standard: `openai:gpt-5-mini`.
- **`LANGUAGE`**: Sprache für den finalen Research-Report. Standard: `german`.
- **`CURATE_SOURCES`**: Legt fest, ob Quellen vor der Recherche kuratiert werden. Dieser Schritt fügt einen zusätzlichen LLM-Lauf hinzu, was Kosten und Laufzeit erhöhen kann, aber die Auswahlqualität verbessert. Standard: `False`.
- **`FAST_TOKEN_LIMIT`**: Maximales Token-Limit für schnelle LLM-Antworten. Standard: `2000`.
- **`SMART_TOKEN_LIMIT`**: Maximales Token-Limit für intelligente LLM-Antworten. Standard: `4000`.
- **`STRATEGIC_TOKEN_LIMIT`**: Maximales Token-Limit für strategische LLM-Antworten. Standard: `4000`.
- **`BROWSE_CHUNK_MAX_LENGTH`**: Maximale Länge der Textabschnitte, die aus Webquellen eingelesen werden. Standard: `8192`.
- **`SUMMARY_TOKEN_LIMIT`**: Maximales Token-Limit für Zusammenfassungen. Standard: `700`.
- **`TEMPERATURE`**: Sampling-Temperatur für LLM-Antworten, typischerweise zwischen 0 und 1. Höhere Werte erzeugen mehr Zufall und Kreativität, niedrigere Werte fokussiertere und deterministischere Antworten. Standard: `0.4`.
- **`USER_AGENT`**: Eigener User-Agent-String für Web-Crawling und Web-Requests.
- **`MAX_SEARCH_RESULTS_PER_QUERY`**: Maximale Anzahl an Suchergebnissen pro Anfrage. Standard: `5`.
- **`MEMORY_BACKEND`**: Backend für Speicheroperationen, etwa die lokale Ablage temporärer Daten. Standard: `local`.
- **`TOTAL_WORDS`**: Maximale Wortzahl für Dokumentenerzeugung oder Verarbeitungsaufgaben. Standard: `1200`.
- **`REPORT_FORMAT`**: Bevorzugtes Format für die Report-Erzeugung. Standard: `APA`. Weitere Formate sind zum Beispiel `MLA`, `CMS`, `Harvard style` und `IEEE`.
- **`MAX_ITERATIONS`**: Maximale Anzahl an Iterationen für Prozesse wie Query-Erweiterung oder Suchverfeinerung. Standard: `3`.
- **`AGENT_ROLE`**: Rolle des Agents. Damit wird das Verhalten spezialisierter Research-Agenten konfiguriert. Standard: `None`. Wenn gesetzt, aktiviert dies domänenspezifische Prompts und Techniken.
- **`MAX_SUBTOPICS`**: Maximale Anzahl an Unterthemen, die erzeugt oder berücksichtigt werden. Standard: `3`.
- **`SCRAPER`**: Web-Scraper zum Sammeln von Informationen. Standard: `bs` (BeautifulSoup). Du kannst auch [newspaper](https://github.com/codelucas/newspaper) verwenden.
- **`MAX_SCRAPER_WORKERS`**: Maximale Anzahl gleichzeitiger Scraper-Worker pro Recherche. Standard: `15`.
- **`REPORT_SOURCE`**: Quelle für die Report-Daten. Standard: `web` für Online-Recherche. Kann auf `doc` für lokale dokumentenbasierte Recherche gesetzt werden. Damit wird festgelegt, woher GPT Researcher seine Primärinformationen bezieht.
- **`DOC_PATH`**: Pfad für lokale Dokumente, die gelesen und recherchiert werden sollen. Standard: `./my-docs`.
- **`PROMPT_FAMILY`**: Die Prompt-Familie und das Prompt-Format, das verwendet werden soll. Standard: auf GPT-Modelle optimierte Prompts. Die vollständige Liste findest du in [enum.py](https://github.com/assafelovic/gpt-researcher/blob/master/gpt_researcher/utils/enum.py#L56).
- **`LLM_KWARGS`**: JSON-formatiertes Dict mit zusätzlichen Keyword-Argumenten für die LLM-Provider-Klasse beim Erzeugen der Instanz. Das ist vor allem für Clients wie Ollama nützlich, die zusätzliche Parameter wie `num_ctx` erlauben.
- **`EMBEDDING_KWARGS`**: JSON-formatiertes Dict mit zusätzlichen Keyword-Argumenten für die Embedding-Provider-Klasse beim Erzeugen der Instanz.
- **`DEEP_RESEARCH_BREADTH`**: Steuert die Breite der Deep-Research-Suche, also wie viele parallele Pfade erkundet werden. Standard: `3`.
- **`DEEP_RESEARCH_DEPTH`**: Steuert die Tiefe der Deep-Research-Suche, also wie viele aufeinanderfolgende Suchen durchgeführt werden. Standard: `2`.
- **`DEEP_RESEARCH_CONCURRENCY`**: Steuert das Parallelitätsniveau für Deep-Research-Operationen. Standard: `4`.
- **`REASONING_EFFORT`**: Steuert den Reasoning-Aufwand strategischer Modelle. Standard: `medium`.

## Deep-Research-Konfiguration

Mit den Deep-Research-Parametern kannst du feinjustieren, wie GPT Researcher komplexe Themen mit umfangreicher Informationssuche erkundet. Zusammen bestimmen sie Gründlichkeit und Effizienz des Rechercheprozesses:

- **`DEEP_RESEARCH_BREADTH`**: Steuert, wie viele parallele Recherchepfade gleichzeitig erkundet werden. Ein höherer Wert, etwa `5`, führt zu mehr unterschiedlichen Unterthemen pro Schritt und damit zu breiterer Abdeckung, aber eventuell weniger Fokus auf die Kernthemen. Der Standardwert `3` ist ein guter Mittelweg.

- **`DEEP_RESEARCH_DEPTH`**: Bestimmt, wie viele aufeinanderfolgende Suchiterationen GPT Researcher pro Pfad durchführt. Höhere Werte, etwa `3-4`, erlauben es, Zitierketten zu verfolgen und tiefer in Spezialwissen einzusteigen, erhöhen aber die Laufzeit deutlich. Der Standardwert `2` hält die Dauer praxisnah.

- **`DEEP_RESEARCH_CONCURRENCY`**: Legt fest, wie viele gleichzeitige Operationen während Deep Research laufen dürfen. Höhere Werte beschleunigen den Prozess auf geeigneten Systemen, können aber API-Limits oder Ressourcenverbrauch erhöhen. Der Standardwert `4` passt für die meisten Umgebungen.

Für akademische oder stark spezialisierte Recherche solltest du Breite und Tiefe eher erhöhen, etwa `BREADTH=4, DEPTH=3`. Für schnelle explorative Recherche liefern niedrigere Werte, etwa `BREADTH=2, DEPTH=1`, schnellere Ergebnisse mit weniger Detail.

Um die Standardkonfiguration zu ändern, kannst du die oben genannten Variablen einfach in deine `.env`-Datei aufnehmen oder sie im lokalen Projektverzeichnis manuell exportieren.

Um zum Beispiel Suchmaschine und Report-Format manuell zu ändern:
```bash
export RETRIEVER=bing
export REPORT_FORMAT=IEEE
```
Beachte, dass du eventuell weitere Umgebungsvariablen exportieren und API-Keys für andere unterstützte Such-Retriever und LLM-Provider beschaffen musst. Die Konsolen-Logs helfen dir bei der Fehlersuche.
Mehr zu zusätzlicher LLM-Unterstützung findest du in der Doku [hier](/docs/gpt-researcher/llms/llms).
