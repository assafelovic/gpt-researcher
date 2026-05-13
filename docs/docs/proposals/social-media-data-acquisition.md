# RFC: Datenbeschaffung von Social-Media-Plattformen

> **Status**: Vorschlag
> **Erstellungsdatum**: 2026-02-01
> **Autor**: GPT-Researcher-Community
> **Zielversion**: v4.x

---

## Inhaltsverzeichnis

1. [Hintergrund und Motivation](#1-hintergrund-und-motivation)
2. [Problemstellung](#2-problemstellung)
3. [Offizielle API-Analyse](#3-offizielle-api-analyse)
4. [Drittanbieter-Plattformen](#4-drittanbieter-plattformen)
5. [Projektinterne Werkzeuge](#5-projektinterne-werkzeuge)
6. [Empfohlene Strategien](#6-empfohlene-strategien)
7. [Technisches Design](#7-technisches-design)
8. [Risiko und Compliance](#8-risiko-und-compliance)
9. [Kostenanalyse](#9-kostenanalyse)
10. [Umsetzungsfahrplan](#10-umsetzungsfahrplan)
11. [Referenzen](#11-referenzen)

---

## 1. Hintergrund und Motivation

GPT-Researcher ist ein starkes automatisiertes Deep-Research-Tool, das Informationen aus dem Web sammelt und hochwertige Berichte erzeugt. Derzeit unterstützt das Projekt unter anderem:

- Suchmaschinen wie Tavily, Google, Bing, DuckDuckGo und Serper
- Web-Scraping mit BeautifulSoup, Selenium, NoDriver und FireCrawl
- Spezielle Formate wie PDFs und ArXiv-Paper
- Lokale Dokumente und Vektordatenbanken

Was fehlt, sind zuverlässige Social-Media-Datenquellen.

Plattformen wie LinkedIn, X und Facebook enthalten wertvolle Signale für Forschung:

| Plattform | Relevante Inhalte |
|------|------|
| LinkedIn | Unternehmensdaten, Branchentrends, Expertenmeinungen, Recruiting-Trends |
| X (Twitter) | Echtzeitereignisse, Stimmungsbilder, Expertenkommentare, technische Diskussionen |
| Facebook | Community-Diskussionen, Nutzerfeedback, lokale Informationen |

---

## 2. Problemstellung

Social-Media-Plattformen sind schwierig zu nutzen, weil:

- Login-Walls viele Inhalte blockieren
- Anti-Bot-Maßnahmen Scraping erschweren
- Offizielle APIs teuer oder stark eingeschränkt sind
- Inhalte oft dynamisch per JavaScript geladen werden
- Rate-Limits und Sperren schnell auftreten

Ziel dieses RFCs ist es, Integrationsoptionen für solche Plattformen zu bewerten und eine praktikable Architektur vorzuschlagen.

---

## 3. Offizielle API-Analyse

### X (Twitter) API

X ist die einzige große Plattform mit einer öffentlich dokumentierten Such-API, aber die Preisstruktur ist für Forschungsanwendungen schwierig:

| Stufe | Monatspreis | Leseleistung | Suchumfang |
|------|------|------|------|
| Free | 0 $ | Kein Lesen | - |
| Basic | 100 $ | 10.000 Tweets/Monat | Nur letzte 7 Tage |
| Pro | 5.000 $ | 1.000.000 Tweets/Monat | Vollarchiv |
| Enterprise | 42.000 $+ | Individuell | Vollarchiv |

Bewertung:
- Vorteil: Offiziell, aktuell, suchbar
- Nachteil: Basic ist für Recherchen zu kurz, Pro ist sehr teuer

### LinkedIn API

LinkedIn ist die geschlossenste der drei Plattformen. Normale Entwickler erhalten nur sehr eingeschränkten Zugriff:

- Login und Teilen funktionieren
- Basis-Profile mit Einwilligung funktionieren
- Suche nach Personen, Firmen und Beiträgen ist praktisch nicht verfügbar

Offizielle Partnerprogramme sind komplex, teuer und genehmigungspflichtig.

### Facebook Graph API

Facebook bietet zwar APIs, aber Forschung auf öffentlichen Beiträgen und Gruppen ist stark eingeschränkt. Vieles ist nur mit App-Freigaben, Nutzer-Einwilligung oder Business-Zugängen möglich.

### Fazit zu offiziellen APIs

Offizielle APIs sind für Deep Research meist:
- zu teuer
- zu eingeschränkt
- zu langsam in der Freischaltung

---

## 4. Drittanbieter-Plattformen

Es gibt mehrere Anbieter, die Social-Media-Daten als Service anbieten, zum Beispiel:

- Apify
- PhantomBuster
- Bright Data
- Data365
- Scrapingdog

Diese Dienste können hilfreich sein, bringen aber Kosten, Vendor-Lock-in und Compliance-Fragen mit sich.

---

## 5. Projektinterne Werkzeuge

GPT Researcher bringt bereits Bausteine mit, die teilweise helfen:

- allgemeine Websuche
- Scraper
- lokale Dokumentenverarbeitung
- MCP-Integration

Für Social Media reicht das allein aber noch nicht aus.

---

## 6. Empfohlene Strategien

### Strategie 1: Apify-Integration

- Gut für schnelle Prototypen
- Gute Abdeckung für viele Plattformen
- Einfach über API integrierbar

### Strategie 2: Bright Data-Integration

- Eher für Enterprise- und Skalierungsszenarien
- Gute Infrastruktur für komplexeres Crawling

### Strategie 3: Hybrider Ansatz

Empfohlen wird ein hybrider Pfad:

1. Offizielle APIs nutzen, wo möglich
2. Drittanbieter-APIs für Lücken ergänzen
3. Ergebnisse normalisieren und gemeinsam bewerten

---

## 7. Technisches Design

Vorgeschlagene Architektur:

```text
User Query
   │
   ▼
Query Planner
   │
   ├── Official API Fetchers
   ├── Third-Party Data Connectors
   └── Existing Web Search / Scraper
   │
   ▼
Normalization Layer
   │
   ▼
Evidence / Verification / Report
```

Wichtige Anforderungen:
- gemeinsames Datenmodell
- Quellenmetadaten
- Deduplizierung
- Compliance-Filter

---

## 8. Risiko und Compliance

Hauptthemen:
- Nutzungsbedingungen der Plattformen
- Datenschutz und persönliche Daten
- Rate-Limit- und Sperrrisiken
- Langzeitstabilität externer Anbieter

---

## 9. Kostenanalyse

Offizielle APIs sind für Forschung oft zu teuer. Drittanbieter sind flexibler, können aber bei hoher Nutzung ebenfalls teuer werden. Für produktive Nutzung ist eine klare Kostenobergrenze sinnvoll.

---

## 10. Umsetzungsfahrplan

1. Anforderungen für Social-Media-Quellen definieren
2. Ein Datenmodell für Plattformquellen anlegen
3. Einen oder zwei Drittanbieter pilotieren
4. Compliance- und Kostenchecks ergänzen
5. Dann systematisch ausbauen

---

## 11. Referenzen

- Offizielle API-Dokumentationen der jeweiligen Plattformen
- Drittanbieter-Dokumentationen
- Interne GPT-Researcher-Architektur und Quellendokumentation
