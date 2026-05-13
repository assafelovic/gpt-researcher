# Mit der CLI ausführen

Dieses Kommandozeilen-Tool (CLI) ermöglicht dir, mit der `GPTResearcher`-Klasse Research-Reports zu erzeugen. So kannst du zu verschiedensten Themen einfach recherchieren und unterschiedliche Report-Typen generieren.

## Installation

1. Repository klonen:
   ```
   git clone https://github.com/assafelovic/gpt-researcher.git
   cd gpt-researcher
   ```

2. Die benötigten Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```

3. Die Umgebungsvariablen einrichten:
   Lege im Projektstamm eine `.env`-Datei an und trage dort deine API-Keys oder andere nötige Konfigurationen ein.

## Nutzung

Die Grundsyntax für die CLI lautet:

```
python cli.py "<query>" --report_type <report_type> [--tone <tone>]
```

### Parameter

- `query` (erforderlich): Die Forschungsfrage, die du untersuchen möchtest.
- `--report_type` (erforderlich): Der zu erzeugende Report-Typ. Mögliche Werte:
  - `research_report`: Zusammenfassung - kurz und schnell (~2 min)
  - `detailed_report`: Detailliert - tiefergehend und länger (~5 min)
  - `resource_report`
  - `outline_report`
  - `custom_report`
  - `subtopic_report`
- `--tone` (optional): Der Ton des Reports. Standard ist `objective`. Mögliche Werte:
  - `objective`: Sachlich und unvoreingenommen
  - `formal`: Akademischer Stil mit gehobener Sprache
  - `analytical`: Kritische Bewertung und Analyse
  - `persuasive`: Überzeugende Perspektive
  - `informative`: Klare und umfassende Information
  - `explanatory`: Verständliche Erklärung komplexer Konzepte
  - `descriptive`: Detaillierte Beschreibung
  - `critical`: Bewertung von Gültigkeit und Relevanz
  - `comparative`: Gegenüberstellung verschiedener Ansätze
  - `speculative`: Erkundung von Hypothesen
  - `reflective`: Persönliche Einblicke
  - `narrative`: Erzählerische Darstellung
  - `humorous`: Locker und unterhaltsam
  - `optimistic`: Fokus auf positive Aspekte
  - `pessimistic`: Fokus auf Herausforderungen

## Beispiele

1. Einen schnellen Research-Report zu Klimawandel erzeugen:
   ```
   python cli.py "What are the main causes of climate change?" --report_type research_report
   ```

2. Einen detaillierten Report über künstliche Intelligenz mit analytischem Ton erstellen:
   ```
   python cli.py "The impact of artificial intelligence on job markets" --report_type detailed_report --tone analytical
   ```

3. Einen Gliederungs-Report zu erneuerbaren Energien mit überzeugendem Ton erzeugen:
   ```
   python cli.py "Renewable energy sources and their potential" --report_type outline_report --tone persuasive
   ```

## Ausgabe

Der erzeugte Report wird als Markdown-Datei im Verzeichnis `outputs` gespeichert. Der Dateiname ist eine eindeutige UUID.

## Hinweis

- Die Ausführungszeit kann je nach Komplexität der Anfrage und gewähltem Report-Typ variieren.
- Stelle sicher, dass die nötigen API-Keys und Berechtigungen in deiner `.env`-Datei korrekt gesetzt sind.
- Alle Ton-Optionen müssen in Kleinbuchstaben angegeben werden.
