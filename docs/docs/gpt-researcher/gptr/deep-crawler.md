# Begrenzter Deep-Crawler

GPT Researcher verlässt sich in diesem Fork nicht auf ein freies, unbegrenztes Crawling. Stattdessen nutzt er eine begrenzte Discovery-Schicht, die Suchtreffer bewertet, nur eine kleine Zahl relevanter Links verfolgt und die resultierende URL-Menge an die bestehende Scraper-Pipeline übergibt.

Das Ziel ist einfach: bessere Quellenabdeckung und höhere Quellenqualität, ohne die Recherche in einen unkontrollierten Spider zu verwandeln.

## Was er macht

- Bewertet Suchergebnisse vor dem Scraping
- Bevorzugt Seiten aus derselben Domain und dokumentationsähnliche Seiten, wenn sie zur Aufgabe passen
- Folgt nur einer begrenzten Anzahl von Links von vielversprechenden Seiten
- Filtert offensichtliches Rauschen wie Login-, Signup-, Datenschutz- und andere Hilfsseiten
- Entfernt doppelte URLs, bevor sie den Scraper erreichen
- Behält die ursprüngliche Reihenfolge der höchstbewerteten URLs bei

## So funktioniert es

Der Discovery-Flow ist implementiert in:

- `gpt_researcher/actions/deep_crawler.py`
- `gpt_researcher/skills/researcher.py`

Auf hoher Ebene läuft das so ab:

1. Such-Retriever liefern Seed-URLs.
2. Jede Kandidaten-URL wird anhand von Query-Overlap, Domain-Präferenz und Docs-/Reference-Hinweisen bewertet.
3. Die besten Kandidaten werden eine Ebene tiefer gecrawlt, indem Hyperlinks aus dem HTML extrahiert werden.
4. Neue Links werden erneut bewertet und gegen die aktuelle Anfrage sowie die Domain-Regeln gefiltert.
5. Die final sortierte Liste geht an die Scraper-Schicht für die normale Inhaltsextraktion.

Das bedeutet: Der Crawler ist ein Discovery-Schritt, kein Ersatz für den Scraper. Er entscheidet *was als Nächstes geholt wird*, während der vorhandene Scraper entscheidet *wie der Inhalt extrahiert wird*.

## Konfiguration

Der Crawler ist standardmäßig aktiviert und kann über diese Einstellungen angepasst werden:

- `ENABLE_DEEP_CRAWLER`
- `DEEP_CRAWLER_DEPTH`
- `DEEP_CRAWLER_BREADTH`
- `DEEP_CRAWLER_CONCURRENCY`
- `DEEP_CRAWLER_MAX_PAGES`
- `DEEP_CRAWLER_MAX_LINKS_PER_PAGE`
- `DEEP_CRAWLER_ALLOW_EXTERNAL_LINKS`
- `DEEP_CRAWLER_TIMEOUT`

Empfohlene Startwerte für die meisten Rechercheaufgaben:

- `DEEP_CRAWLER_DEPTH=1`
- `DEEP_CRAWLER_BREADTH=4`
- `DEEP_CRAWLER_MAX_PAGES=12`
- `DEEP_CRAWLER_ALLOW_EXTERNAL_LINKS=false`

## Wann er hilft

Der begrenzte Crawler ist besonders nützlich für:

- API documentation
- SDK references
- product manuals
- developer guides
- knowledge-base articles

Weniger nützlich ist er für:

- broad news research
- highly heterogeneous search spaces
- tasks where every result is intentionally unrelated but still useful

## Validierung

Der Crawler wird abgedeckt durch:

- `tests/test_deep_crawler.py`
- `tests/test_query_planner_hardening.py`

Diese Tests prüfen:

- Docs-Seiten werden gegenüber offensichtlichen Noise-Seiten höher bewertet
- Same-Domain-Links werden entdeckt und behalten
- Der Research-Conductor erhält die Reihenfolge des Crawlers

## Praktische Wirkung

Bei einer Anfrage wie „FastAPI async API docs“ bevorzugt der Crawler offizielle Dokumentationspfade und stuft Seiten wie Login- oder Account-Flows niedriger ein. Bei einer breiteren Anfrage bleibt er trotzdem begrenzt und fächert nicht endlos rekursiv auf.
