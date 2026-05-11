# Deep Research ✨ NEU ✨

Mit dem jüngsten „Deep Research“-Trend in der KI-Community freuen wir uns, unsere eigene Open-Source-Deep-Research-Fähigkeit vorzustellen. GPT Researchers Deep Research ist ein fortgeschrittenes rekursives Forschungssystem, das Themen mit außergewöhnlicher Tiefe und Breite erkundet.

## So funktioniert es

Deep Research nutzt ein baumartiges Erkundungsmuster:

1. **Breite**: Auf jeder Ebene werden mehrere Suchanfragen erzeugt, um verschiedene Aspekte des Themas abzudecken
2. **Tiefe**: Für jeden Zweig wird rekursiv weiter in die Tiefe gegangen, um Hinweise zu verfolgen und Verbindungen aufzudecken
3. **Parallele Verarbeitung**: Async/Await wird genutzt, um mehrere Recherchepfade gleichzeitig auszuführen
4. **Intelligentes Kontextmanagement**: Erkenntnisse aus allen Zweigen werden automatisch zusammengeführt und verdichtet
5. **Fortschrittsanzeige**: Echtzeit-Updates zum Forschungsfortschritt über Breite und Tiefe hinweg

Stell dir vor, du setzt ein Team von KI-Forschern ein, die jeweils ihren eigenen Weg verfolgen, aber zusammenarbeiten, um ein umfassendes Verständnis des Themas aufzubauen.

## Ablauf
![deep research](https://github.com/user-attachments/assets/eba2d94b-bef3-4f8d-bbc0-f15bd0a40968)

## Schnellstart

```python
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
import asyncio

async def main():
    # Researcher mit Deep-Research-Typ initialisieren
    researcher = GPTResearcher(
        query="Was sind die neuesten Entwicklungen im Bereich Quantencomputing?",
        report_type="deep",  # Löst den Deep-Research-Modus aus
    )
    
    # Recherche ausführen
    research_data = await researcher.conduct_research()
    
    # Bericht erzeugen
    report = await researcher.write_report()
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

## Konfiguration

Das Verhalten von Deep Research kann über mehrere Parameter angepasst werden:

- `deep_research_breadth`: Anzahl der parallelen Recherchepfade pro Ebene (Standard: 4)
- `deep_research_depth`: Wie viele Ebenen tief gesucht wird (Standard: 2)
- `deep_research_concurrency`: Maximale Anzahl gleichzeitiger Recherchevorgänge (Standard: 2)

Du kannst diese Werte in deiner Config-Datei setzen, als Umgebungsvariablen übergeben oder direkt beim Aufruf setzen:

```python
researcher = GPTResearcher(
    query="deine Anfrage",
    report_type="deep",
    config_path="path/to/config.yaml"  # Hier die Deep-Research-Parameter konfigurieren
)
```

## Fortschrittsanzeige

Der `on_progress`-Callback liefert Echtzeit-Einblicke in den Forschungsprozess:

```python
class ResearchProgress:
    current_depth: int       # Aktuelle Tiefenebene
    total_depth: int         # Maximale Tiefe
    current_breadth: int     # Aktuelle Anzahl paralleler Pfade
    total_breadth: int       # Maximale Breite pro Ebene
    current_query: str       # Aktuell verarbeitete Anfrage
    completed_queries: int   # Anzahl abgeschlossener Anfragen
    total_queries: int       # Gesamtzahl der zu verarbeitenden Anfragen
```

## Erweiterte Nutzung

### Eigener Research-Flow

```python
researcher = GPTResearcher(
    query="deine Anfrage",
    report_type="deep",
    tone=Tone.Objective,
    headers={"User-Agent": "dein-agent"},  # Eigene Header für Webanfragen
    verbose=True  # Detailliertes Logging aktivieren
)

# Rohdaten der Recherche abrufen
context = await researcher.conduct_research()

# Recherchequellen abrufen
sources = researcher.get_research_sources()

# Besuchte URLs abrufen
urls = researcher.get_source_urls()

# Formatierten Bericht erzeugen
report = await researcher.write_report()
```

### Fehlerbehandlung

Das Deep-Research-System ist robust ausgelegt:

- Fehlgeschlagene Anfragen werden automatisch übersprungen
- Die Recherche läuft weiter, auch wenn einzelne Zweige fehlschlagen
- Die Fortschrittsanzeige hilft dabei, Probleme schnell zu erkennen

## Best Practices

1. **Breit beginnen**: Starte mit einer allgemeinen Anfrage und lasse das System Details erkunden
2. **Fortschritt beobachten**: Nutze den Fortschritts-Callback, um den Ablauf zu verstehen
3. **Parameter anpassen**: Justiere Breite und Tiefe je nach Bedarf:
   - Mehr Breite = größere Abdeckung
   - Mehr Tiefe = tiefere Einsichten
4. **Ressourcenmanagement**: Berücksichtige die Konnektivität und Rechenleistung deines Systems

## Einschränkungen

- Nutzung von Reasoning-LLMs wie `o3-mini`. Dafür sind Reasoning-Berechtigungen erforderlich und der Lauf wird deutlich langsamer.
- Deep Research kann länger dauern als normale Recherche
- Höherer API-Verbrauch und höhere Kosten durch mehrere gleichzeitige Anfragen
- Möglicherweise mehr Systemressourcen für parallele Verarbeitung nötig

Viel Erfolg bei der Recherche! 🎉
