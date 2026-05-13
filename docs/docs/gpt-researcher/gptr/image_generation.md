---
sidebar_label: Bildgenerierung
sidebar_position: 5
---

# 🍌 Inline-Bildgenerierung

GPT Researcher unterstützt **Inline-Bildgenerierung** für Research-Reports mit den Bildmodellen von Google Gemini (Nano Banana). Diese Funktion erstellt kontextuell passende Illustrationen, die direkt in den Report eingebettet werden.

## Überblick

Wenn die Funktion aktiviert ist, dann:
1. **analysiert GPT Researcher den Research-Kontext** und sucht nach sinnvollen Visualisierungen
2. **werden Bilder vorab generiert**, bevor der Report geschrieben wird
3. **werden die Bilder inline eingebettet** - ohne zusätzliche Wartezeit nach dem Schreiben

## Schnellstart

### 1. Umgebungsvariablen setzen

```bash
# Erforderlich: Feature aktivieren
IMAGE_GENERATION_ENABLED=true

# Erforderlich: Dein Google API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Modell angeben (Standardwert gezeigt)
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image

# Optional: Maximale Bilder pro Report (Standard: 3)
IMAGE_GENERATION_MAX_IMAGES=3

# Optional: Bildstil - "dark" (Standard), "light" oder "auto"
IMAGE_GENERATION_STYLE=dark
```

### 2. Recherche starten

```python
import asyncio
from gpt_researcher import GPTResearcher

async def main():
    researcher = GPTResearcher(
        query="Was sind die wichtigsten Komponenten eines modernen Solarpanelsystems?",
        report_type="research_report"
    )

    # Bilder werden automatisch während der Recherche generiert
    await researcher.conduct_research()

    # Der Report enthält eingebettete Bilder
    report = await researcher.write_report()
    print(report)

asyncio.run(main())
```

Fertig. Die Bilder werden automatisch erzeugt und im Report eingebettet.

## So funktioniert es

### Der smarte Vorab-Generierungs-Flow

```
Research-Phase          Bildplanung            Report-Schreiben
     │                       │                       │
     ▼                       ▼                       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│ Informationen│      │ LLM analysiert│      │ Report streamt  │
│ sammeln     │  →   │ den Kontext   │  →   │ mit Bildern     │
│ aus Quellen  │      │ für 2-3 Visuals│     │ bereits inline! │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Alle Bilder  │
                     │ parallel     │
                     │ generieren   │
                     └──────────────┘
```

**Vorteile:**
- **Kein Warten** - Bilder werden während der Recherche generiert, nicht danach
- **Nahtlose UX** - Der Report streamt bereits mit eingebetteten Bildern
- **Kontextbewusst** - Das LLM wählt die besten Visualisierungsmöglichkeiten aus

## Konfigurationsoptionen

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|---------|-------------|
| `IMAGE_GENERATION_ENABLED` | `false` | Hauptschalter zum Aktivieren/Deaktivieren |
| `GOOGLE_API_KEY` | - | Dein Google API Key (erforderlich) |
| `IMAGE_GENERATION_MODEL` | `models/gemini-2.5-flash-image` | Zu verwendendes Gemini-Modell |
| `IMAGE_GENERATION_MAX_IMAGES` | `3` | Maximale Bilder pro Report |
| `IMAGE_GENERATION_STYLE` | `dark` | Bildstil: `dark`, `light`, `auto` |

### Unterstützte Modelle

**Kostenlose Stufe (Gemini):**
| Modell | Beschreibung |
|-------|-------------|
| `models/gemini-2.5-flash-image` | Empfohlen - schnell und kostenlos |
| `gemini-2.0-flash-exp-image-generation` | Experimentelle Variante |

**Bezahlte Stufe (Imagen) - erfordert Google Cloud Billing:**
| Modell | Beschreibung |
|-------|-------------|
| `imagen-4.0-generate-001` | Höchste Qualität, unterstützt Seitenverhältnisse |
| `imagen-4.0-fast-generate-001` | Schnellere Generierung |

## Bildstil

### Dunkler Modus (Standard)

Die Bilder werden mit einem Stil erzeugt, der zur GPT-Researcher-UI passt:
- Dunkler Hintergrund (`#0d1117`)
- Teal-/Cyan-Akzente (`#14b8a6`)
- Leuchtende, futuristische Ästhetik
- Professioneller Infografik-Stil

### Heller Modus

Setze `IMAGE_GENERATION_STYLE=light` für:
- Klare weiße/hellgraue Hintergründe
- Dunkelblaue und tealfarbene Akzente
- Ein Corporate-/Professional-Look

### Auto-Modus

Setze `IMAGE_GENERATION_STYLE=auto` für ein neutrales Styling, das in jedem Kontext funktioniert.

## Ausgabe

### Bildspeicherung

Generierte Bilder werden gespeichert unter:
```
outputs/images/{research_id}/img_{hash}_{index}.png
```

### Markdown-Einbettung

Die Bilder werden mit der normalen Markdown-Syntax eingebettet:
```markdown
## Systemarchitektur

![Übersicht der Systemarchitektur](/outputs/images/research_abc123/img_def456_0.png)

Die Architektur besteht aus drei Hauptkomponenten...
```

### Darstellung im Frontend

Im Next.js-Frontend werden die Bilder über die Route `/outputs/` ausgeliefert, die an das Backend weiterleitet. Die Bilder erscheinen mit 75 % Breite und tealfarbenen Akzentrahmen.

## WebSocket-Events

Bei Nutzung der Weboberfläche werden diese Events gesendet:

| Event | Beschreibung |
|-------|-------------|
| `image_planning` | Kontext für Visuals analysieren |
| `image_concepts_identified` | N Visualisierungsmöglichkeiten gefunden |
| `image_generating` | Bild X von Y wird generiert |
| `images_ready` | Alle Bilder erfolgreich erzeugt |

## Best Practices

1. **Für detaillierte Reports aktivieren** - Am besten für `research_report` und `detailed_report`
2. **API-Nutzung im Blick behalten** - Die Free Tier hat Tageslimits. Mit `IMAGE_GENERATION_MAX_IMAGES=2` sparst du Kontingent
3. **Dunklen Modus verwenden** - Der Standardstil passt zur App und wirkt professionell
4. **Erzeugte Bilder prüfen** - KI-Bilder brauchen gelegentlich manuelle Nachkontrolle

## Fehlerbehebung

### Bilder werden nicht erzeugt

1. Prüfe `IMAGE_GENERATION_ENABLED=true`
2. Prüfe, ob `GOOGLE_API_KEY` gesetzt und gültig ist
3. Stelle sicher, dass der Modellname korrekt ist (bei Gemini mit `models/`-Prefix)
4. Prüfe die Logs auf API-Fehler

### Kontingent überschritten

Wenn `RESOURCE_EXHAUSTED`-Fehler auftauchen:
- Warte bis Mitternacht UTC auf den täglichen Reset
- Reduziere `IMAGE_GENERATION_MAX_IMAGES`
- Aktiviere Google Cloud Billing für höhere Kontingente
- Erstelle ein neues Google-Cloud-Projekt für frisches Kontingent

### Bilder werden im Frontend nicht angezeigt

1. Stelle sicher, dass das Next.js-Frontend den `/outputs`-Proxy verwendet
2. Prüfe, ob das Backend statische Dateien aus `outputs/` ausliefert
3. Verifiziere, dass die Bildpfade im Markdown korrekt sind

## Bildgenerierung deaktivieren

Zum vollständigen Deaktivieren:
```bash
IMAGE_GENERATION_ENABLED=false
```

Oder setze einfach keine `IMAGE_GENERATION_*`-Variablen - die Funktion ist standardmäßig aus.
