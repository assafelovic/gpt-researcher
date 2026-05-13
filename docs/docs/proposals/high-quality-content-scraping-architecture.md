# RFC: Architektur für hochwertige Inhalts- und Bildextraktion

> **Status**: Vorschlag
> **Autor**: Community-Mitwirkende
> **Erstellungsdatum**: 2026-01-31
> **Zielversion**: v4.x

## Überblick

Dieser Vorschlag analysiert die aktuellen Scraping-Fähigkeiten von GPT-Researcher und empfiehlt eine bessere Architektur, um hochwertige Textinhalte und passende Bilder aus Webquellen zu gewinnen.

---

## Inhaltsverzeichnis

1. [Aktuelle Architektur](#1-aktuelle-architektur)
2. [Interne und externe Tools](#2-interne-und-externe-tools)
3. [Empfohlene Hybridarchitektur](#3-empfohlene-hybridarchitektur)
4. [Implementierungsleitfaden](#4-implementierungsleitfaden)
5. [Entscheidungsmatrix](#5-entscheidungsmatrix)
6. [Kostenanalyse](#6-kostenanalyse)

---

## 1. Aktuelle Architektur

Die derzeitige Pipeline arbeitet grob so:

1. Der Nutzer stellt eine Frage
2. Tavily liefert URLs und kurze Snippets
3. GPT Researcher extrahiert URLs und scrapt die Seiten separat erneut
4. Die Inhalte werden in Chunks zerlegt und per Vektorfilterung verdichtet

Das Problem dabei:
- Tavily-Summaries werden nicht voll genutzt
- raw_content fehlt oft
- Bilder werden nicht sauber mitgenommen
- JS-lastige Seiten sind schwierig

---

## 2. Interne und externe Tools

### Interne Werkzeuge

- BeautifulSoup: schnell, aber schwach bei JS und Anti-Bot
- Browser/Selenium: gut für JS, aber langsam und ressourcenintensiv
- NoDriver: flexibler, aber komplexer
- PyMuPDF: gut für PDFs
- ArXiv-Loader: gut für wissenschaftliche Paper

### Externe Werkzeuge

- Tavily Extract: saubere Inhalte, aber kostenpflichtig
- FireCrawl: stark für JS-Inhalte und saubere Extraktion
- Tavily Search Advanced: Suchergebnisse mit raw content und Bildern

---

## 3. Empfohlene Hybridarchitektur

Empfohlen wird ein zweistufiger Ansatz:

1. **Phase 1: Suche mit Tavily Search Advanced**
   - raw_content nutzen, wenn verfügbar
   - Bilder und Bildbeschreibungen mitnehmen
   - URL- und Inhaltsmetadaten speichern

2. **Phase 2: Fallback-Crawling**
   - Wenn raw_content fehlt oder zu kurz ist, Browser/NoDriver/FireCrawl nutzen
   - Nur dort nachscrapen, wo es wirklich nötig ist

So lassen sich Kosten, Geschwindigkeit und Qualität besser balancieren.

---

## 4. Implementierungsleitfaden

### Empfohlene Reihenfolge

1. Ergebnisstruktur erweitern, damit raw_content und Bilder gespeichert werden
2. Fallback-Regeln für JS- und leere Seiten definieren
3. Bildsammlung aus Suchergebnissen und HTML-Quellen vereinen
4. Relevanzfilter und Deduplizierung verbessern

### Ziel

- weniger redundante Requests
- bessere Textqualität
- mehr relevante Bilder
- stabilere Verarbeitung moderner Webanwendungen

---

## 5. Entscheidungsmatrix

| Werkzeug | Stärken | Schwächen |
|------|------|------|
| BeautifulSoup | Schnell, einfach | Schlechte JS-Unterstützung |
| Browser | JS-fähig | Langsam |
| NoDriver | Tarnung besser | Komplexer |
| Tavily Extract | Saubere Inhalte | Kostenpflichtig |
| FireCrawl | Sehr gute Extraktion | Extern, kostenpflichtig |

---

## 6. Kostenanalyse

Die Kosten steigen vor allem dann, wenn:
- viele Seiten erneut gecrawlt werden
- JS-lastige Seiten verarbeitet werden
- Bilder zusätzlich extrahiert werden

Der beste Weg ist daher, möglichst viele Inhalte aus der ersten Suchphase mitzunehmen und nur gezielt Fallback-Scraping zu nutzen.

---

## Fazit

Die aktuelle Architektur funktioniert, verschenkt aber Potenzial. Ein hybrider Ansatz mit besserer Nutzung von `raw_content`, gezieltem Fallback und konsistenter Bildverarbeitung würde die Qualität der extrahierten Inhalte deutlich verbessern.
