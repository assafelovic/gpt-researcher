# RFC: Adaptive Deep Research - Qualitätsgesteuerte rekursive Suche

> **Status**: Vorschlag
> **Autor**: Community-Mitwirkende
> **Erstellungsdatum**: 2026-01-30
> **Zielversion**: v4.x

## Überblick

Dieser Vorschlag führt einen **adaptiven Deep-Research-Modus** ein, der mithilfe einer LLM-basierten Qualitätsbewertung dynamisch bestimmt, wie tief gesucht wird, statt mit einer festen Rekursionstiefe zu arbeiten.

## Motivation

### Grenzen des aktuellen Designs

Die derzeitige Deep-Research-Implementierung arbeitet mit einer festen Tiefe:

```python
# Aktuelles Verhalten
depth = 2  # fester Wert
breadth = 4

# Unabhängig von der Komplexität werden immer genau 2 Runden ausgeführt
```

Probleme dieses Ansatzes:

| Problem | Beschreibung |
|------|------|
| **Ressourcenverschwendung** | Einfache Anfragen durchlaufen trotzdem die volle Tiefe |
| **Zu wenig Tiefe** | Komplexe Anfragen brauchen oft mehr als 2 Runden |
| **Keine Qualitätskontrolle** | Abbruch basiert auf Zählwerten statt auf Qualität |
| **Unflexibel** | Ein starres Schema passt nicht zu allen Aufgaben |

### Vorgeschlagene Lösung

Ein **qualitätsgesteuerter adaptiver Loop**: Nach jeder Runde bewertet ein LLM-Reviewer die Qualität und entscheidet, ob weiter gesucht oder beendet wird.

```text
┌─────────────────────────────────────────────────────────────────┐
│                 Aktuelles Design vs. Vorschlag                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Aktuell (feste Tiefe):                                         │
│  Suche → Suche → Stopp (immer 2 Runden)                         │
│                                                                 │
│  Vorschlag (adaptiv):                                           │
│  Suche → Bewertung → [Qualität gut genug?] → Ja → Stopp        │
│                          │                                      │
│                          └─→ Nein → Suche → Bewertung → ...     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Detailliertes Design

### 1. Architektur

```text
┌─────────────────────────────────────────────────────────────────┐
│                Adaptiver Deep-Research-Flow                      │
└─────────────────────────────────────────────────────────────────┘

                     Nutzeranfrage
                          │
                          ▼
                 ┌────────────────┐
                 │  Forschungsrunde│
                 │ (conduct_research)
                 └────────┬───────┘
                          │
                          ▼
                 ┌────────────────┐
                 │  Qualitätscheck │  ← LLM-Bewertung
                 │ (assess_quality)│
                 └────────┬───────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
    ┌────────────────┐         ┌────────────────┐
    │ Score >= 7/10  │         │ Score < 7/10   │
    │ oder Max-Tiefe │         │ und Wissenslücken│
    └────────┬───────┘         └────────┬───────┘
             │                         │
             ▼                         ▼
    ┌────────────────┐         ┌────────────────┐
    │   Finaler      │         │ Nächste Runde  │
    │   Bericht      │         │ aus Lücken ableiten │
    └────────────────┘         └────────┬───────┘
                                         │
                                         └──→ zurück zur Forschung
```

### 2. Kernkomponenten

#### 2.1 `AdaptiveDeepResearchSkill`

```python
# gpt_researcher/skills/adaptive_deep_research.py

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import asyncio
import json

from gpt_researcher.llm_provider import create_chat_completion
from gpt_researcher.config import Config


@dataclass
class QualityAssessment:
    """Qualitätsbewertung durch ein LLM"""
    score: float
    dimensions: Dict[str, float]
    reasoning: str
    has_knowledge_gaps: bool
    knowledge_gaps: List[str]
    suggested_directions: List[str]


@dataclass
class AdaptiveResearchProgress:
    """Fortschritt der adaptiven Forschung"""
    current_depth: int
    quality_score: float
    total_queries: int
    knowledge_gaps_remaining: int
    status: str  # "researching", "evaluating", "completed"


class AdaptiveDeepResearchSkill:
    """
    Adaptive Deep-Research-Skill

    Nutzt eine LLM-Qualitätsbewertung, um dynamisch zu entscheiden,
    wann die Recherche beendet werden soll.
    """

    def __init__(self, researcher):
        self.researcher = researcher
        self.cfg: Config = researcher.cfg

        self.min_depth = 1
        self.max_depth = 5
        self.quality_threshold = 7.0
        self.breadth = 4
        self.concurrency_limit = 2

        self.learnings: List[str] = []
        self.context: List[str] = []
        self.citations: Dict[str, str] = {}
        self.visited_urls: Set[str] = set()

        self.current_depth = 0
        self.quality_history: List[QualityAssessment] = []

    async def run(self, query: str, on_progress: Optional[callable] = None) -> Dict[str, Any]:
        self.original_query = query
        return await self._adaptive_research_loop(query=query, on_progress=on_progress)
```

### 3. Ablauf

1. Recherche ausführen
2. Qualität bewerten
3. Bei guter Qualität beenden
4. Bei Lücken gezielt nachrecherchieren

### 4. Vorteile

- Weniger Ressourcenverschwendung
- Bessere Qualität bei komplexen Aufgaben
- Flexibler als ein fester Tiefenwert
- Transparenter Abbruch auf Basis von Bewertung statt reiner Zählwerte

### 5. Implementierungsplan

1. Qualitätsbewertung als LLM-Node ergänzen
2. Wissenslücken ausgeben und speichern
3. Rekursion nur bei schlechter Qualität fortsetzen
4. Metriken und Tests für Qualitätsentscheidungen ergänzen

## Zusammenfassung

Adaptive Deep Research würde GPT Researcher deutlich robuster und effizienter machen, weil die Tiefe der Recherche nicht mehr starr vorgegeben ist, sondern vom tatsächlichen Rechercheergebnis abhängt.
