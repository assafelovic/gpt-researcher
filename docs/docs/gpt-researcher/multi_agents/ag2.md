# AG2

[AG2](https://github.com/ag2ai/ag2) ist ein Framework für Multi-Agent-Anwendungen mit LLMs.
Dieses Beispiel nutzt AG2, um den GPT-Researcher-Multi-Agent-Workflow zu orchestrieren.

Schau dir auch diese Blogposts an:
- [Deep Web Research mit AG2 und GPT Researcher](https://docs.ag2.ai/latest/docs/blog/#deep-web-research-with-ag2-and-gpt-researcher) (AG2-Blog)

## Anwendungsfall

Mit AG2 lässt sich der Rechercheprozess in Tiefe und Qualität verbessern, weil mehrere Agenten mit spezialisierten Fähigkeiten zusammenarbeiten.
Inspiriert von der [STORM](https://arxiv.org/abs/2402.14207)-Arbeit zeigt dieses Beispiel, wie ein Team von KI-Agenten ein Thema von der Planung bis zur Veröffentlichung bearbeitet.

Ein durchschnittlicher Lauf erzeugt einen 5- bis 6-seitigen Research-Report in Formaten wie PDF, DOCX und Markdown.

Hinweis: Dieses Beispiel verwendet die OpenAI-API nur für optimierte Performance.

## Das Multi-Agent-Team

Das Rechercheteam besteht aus 8 Agenten:
- **Human** - Der Mensch im Loop, der den Prozess überwacht und Feedback gibt
- **Chief Editor** - Überwacht den Prozess und koordiniert das Team
- **Researcher** (`gpt-researcher`) - Ein spezialisierter autonomer Agent für tiefgehende Recherche
- **Editor** - Plant Gliederung und Struktur des Reports
- **Reviewer** - Prüft die Korrektheit der Ergebnisse anhand definierter Kriterien
- **Revisor** - Überarbeitet die Ergebnisse anhand des Feedbacks
- **Writer** - Schreibt den finalen Report
- **Publisher** - Veröffentlicht den finalen Report in verschiedenen Formaten

## So funktioniert es

![AG2 Pipeline](/img/ag2-pipeline.webp)

Phasen:
1. Planungsphase
2. Datensammlung und Analyse
3. Review und Überarbeitung
4. Schreiben und Einreichen
5. Veröffentlichung

## So startest du es

1. Benötigte Pakete installieren:
    ```bash
    pip install -r requirements.txt
    pip install -r multi_agents_ag2/requirements.txt
    ```
2. Umgebungsvariablen setzen:
    ```bash
    export OPENAI_API_KEY={Your OpenAI API Key here}
    export TAVILY_API_KEY={Your Tavily API Key here}
    ```
3. Anwendung starten:
    ```bash
    python -m multi_agents_ag2.main
    ```

## Nutzung

Um die Forschungsfrage oder den Report anzupassen, bearbeite `multi_agents_ag2/task.json`.

### `task.json` enthält diese Felder:
- `query` - Die Forschungsfrage oder Aufgabe
- `model` - Das für die Agenten zu nutzende OpenAI-LLM
- `max_sections` - Maximale Anzahl an Abschnitten im Report
- `max_revisions` - Maximale Reviewer/Revisor-Schleifen pro Abschnitt
- `include_human_feedback` - Wenn `true`, kann der Nutzer Feedback geben
- `publish_formats` - Formate, in denen der Report veröffentlicht wird
- `source` - Die Quelle für die Recherche (`web` oder `local`)
- `follow_guidelines` - Wenn `true`, werden die unten definierten Leitlinien befolgt
- `guidelines` - Liste von Leitlinien für den Report
- `verbose` - Wenn `true`, werden detaillierte Logs auf der Konsole ausgegeben
