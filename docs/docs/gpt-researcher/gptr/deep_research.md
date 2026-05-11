# Deep Research ✨ NEU ✨

Mit dem aktuellen Deep-Research-Trend in der KI-Community freuen wir uns, unsere eigene Open-Source-Deep-Research-Funktion bereitzustellen. GPT Researchers Deep Research ist ein fortgeschrittenes rekursives Forschungssystem, das Themen mit ungewöhnlicher Tiefe und Breite erkundet.

Ein Deep-Research-Lauf dauert etwa 5 Minuten und kostet ungefähr 0,40 US-Dollar, wenn `o3-mini` mit `high` Reasoning-Effort verwendet wird.

## So funktioniert es

Deep Research nutzt ein baumartiges Explorationsmuster:

1. **Breite**: Auf jeder Ebene werden mehrere Suchanfragen erzeugt, um unterschiedliche Aspekte des Themas abzudecken
2. **Tiefe**: Jeder Zweig wird rekursiv weiterverfolgt, um Hinweise und Zusammenhänge zu entdecken
3. **Parallele Verarbeitung**: Über `async/await` werden mehrere Recherchepfade gleichzeitig ausgeführt
4. **Intelligentes Kontextmanagement**: Erkenntnisse aus allen Zweigen werden automatisch aggregiert und verdichtet
5. **Fortschrittsanzeige**: Der Recherchefortschritt wird live über Breite und Tiefe hinweg angezeigt

Stell dir das wie ein Team von KI-Forschenden vor, das parallel an verschiedenen Pfaden arbeitet und gemeinsam ein umfassendes Bild des Themas aufbaut.

## Prozessfluss

<img src="https://github.com/user-attachments/assets/eba2d94b-bef3-4f8d-bbc0-f15bd0a40968" alt="Logo" width="568"></img>
<br></br>

## Schnellstart

```python
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
import asyncio

async def main():
    # Researcher mit Deep-Research-Typ initialisieren
    researcher = GPTResearcher(
        query="Was sind die neuesten Entwicklungen im Quantencomputing?",
        report_type="deep",  # Das aktiviert Deep Research
    )

    # Recherche ausführen
    research_data = await researcher.conduct_research()

    # Report erzeugen
    report = await researcher.write_report()
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

## Konfiguration

Das Deep-Research-Verhalten lässt sich über mehrere Parameter steuern:

- `deep_research_breadth`: Anzahl paralleler Recherchepfade pro Ebene (Standard: 4)
- `deep_research_depth`: Wie viele Ebenen tief gesucht wird (Standard: 2)
- `deep_research_concurrency`: Maximale Anzahl gleichzeitiger Rechercheoperationen (Standard: 4)
- `total_words`: Gesamtwortzahl des erzeugten Reports (Empfehlung: 2000)

Diese Parameter kannst du auf verschiedene Arten setzen:

1. **Umgebungsvariablen**:
```bash
export DEEP_RESEARCH_BREADTH=4
export DEEP_RESEARCH_DEPTH=2
export DEEP_RESEARCH_CONCURRENCY=4
export TOTAL_WORDS=2500
```

2. **Konfigurationsdatei**:
```yaml
deep_research_breadth: 4
deep_research_depth: 2
deep_research_concurrency: 4
total_words: 2500
```

```python
researcher = GPTResearcher(
    query="deine Anfrage",
    report_type="deep",
    config_path="pfad/zur/config.yaml"  # Deep-Research-Parameter hier setzen
)
```

## Fortschrittsanzeige

Der `on_progress`-Callback liefert Live-Einblicke in den Rechercheprozess:

```python
class ResearchProgress:
    current_depth: int       # Aktuelle Tiefe
    total_depth: int         # Maximale Tiefe
    current_breadth: int     # Aktuelle Anzahl paralleler Pfade
    total_breadth: int       # Maximale Breite pro Ebene
    current_query: str       # Aktuell verarbeitete Query
    completed_queries: int   # Anzahl abgeschlossener Queries
    total_queries: int       # Gesamtzahl der zu verarbeitenden Queries
```

## Fehlerbehandlung

Der Deep-Research-Workflow ist auf Robustheit ausgelegt:

- Fehlgeschlagene Queries werden automatisch übersprungen
- Die Recherche läuft weiter, auch wenn einige Zweige scheitern
- Die Fortschrittsanzeige hilft dabei, Probleme zu erkennen

## Best Practices

1. **Breit starten**: Beginne mit einer allgemeinen Anfrage und lass das System Details erkunden
2. **Fortschritt beobachten**: Nutze den Progress-Callback, um den Verlauf nachzuvollziehen
3. **Parameter anpassen**: Justiere Breite und Tiefe nach Bedarf:
   - Mehr Breite = breitere Abdeckung
   - Mehr Tiefe = tiefere Einblicke
4. **Ressourcen im Blick behalten**: Berücksichtige die Concurrency-Limits deines Systems

## Grenzen

- Der Einsatz von Reasoning-LLMs wie `o3-mini`
- Deep Research kann länger dauern als Standard-Recherche
- Höhere API-Kosten durch mehrere parallele Abfragen
- Mehr Systemressourcen für parallele Verarbeitung können nötig sein

Viel Erfolg bei der Recherche! 🎉
