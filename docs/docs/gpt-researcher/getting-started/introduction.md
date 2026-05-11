# Einführung

[![Official Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted)](https://discord.gg/QgZXvJAccX)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)

**[GPT Researcher](https://gptr.dev) ist ein autonomer Agent für umfassende Online-Recherche zu verschiedensten Aufgaben.**

Der Agent erstellt detaillierte, faktenbasierte und ausgewogene Research-Reports. Dabei kannst du ihn auf relevante Quellen, Gliederungen und Ergebnisformen ausrichten. Inspiriert von den Arbeiten [Plan-and-Solve](https://arxiv.org/abs/2305.04091) und [RAG](https://arxiv.org/abs/2005.11401) adressiert GPT Researcher die Themen Geschwindigkeit, Determinismus und Verlässlichkeit. Durch parallele Agentenarbeit statt synchroner Abläufe wird die Performance stabiler und oft auch schneller.

## Warum GPT Researcher?

- Objektive Schlussfolgerungen für manuelle Recherchen zu bilden kostet Zeit, manchmal sogar Wochen, bis die richtigen Quellen und Informationen gefunden sind.
- Aktuelle LLMs sind auf vergangene und veraltete Informationen trainiert und bringen ein hohes Halluzinationsrisiko mit sich. Für Rechercheaufgaben sind sie deshalb nur eingeschränkt geeignet.
- Viele LLMs sind auf kurze Ausgaben begrenzt, was für lange, detaillierte Research-Reports nicht ausreicht.
- Lösungen mit Websuche, etwa ChatGPT mit Web-Plugin, berücksichtigen meist nur wenige Quellen. Das führt teils zu oberflächlichen Schlüssen oder verzerrten Antworten.
- Wenn nur ein kleiner Ausschnitt an Quellen verwendet wird, entsteht leicht Bias bei der Beurteilung von Forschungsfragen oder Aufgaben.

## Architektur
Die Grundidee ist, „Planner“- und „Execution“-Agenten zu betreiben. Der Planner erzeugt Forschungsfragen, und die Execution-Agenten suchen die passendsten Informationen zu jeder Frage. Anschließend filtert und aggregiert der Planner alle relevanten Informationen und erstellt den Research-Report. <br /><br />
Die Agenten nutzen sowohl gpt-4o-mini als auch gpt-4o mit 128K Kontext, um eine Aufgabe zu bearbeiten. Wir optimieren die Kosten, indem wir jeweils nur dann das größere Modell verwenden, wenn es nötig ist. **Eine typische Research-Aufgabe dauert etwa 3 Minuten und kostet rund 0,10 US-Dollar.**

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527" />
</div>


Konkret bedeutet das:
* Einen auf das Thema spezialisierten Agenten auf Basis der Forschungsfrage oder Aufgabe erstellen.
* Eine Menge an Forschungsfragen erzeugen, die zusammen ein objektives Bild der Aufgabe ergeben.
* Für jede Forschungsfrage einen Crawler-Agenten starten, der Online-Quellen mit relevanten Informationen durchsucht.
* Für jede gesammelte Quelle die relevanten Informationen zusammenfassen und die Herkunft dokumentieren.
* Am Ende alle zusammengefassten Quellen filtern, aggregieren und daraus den finalen Research-Report erzeugen.

## Demo
<iframe height="400" width="700" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

## Tutorials
 - [Video-Tutorial-Reihe](https://www.youtube.com/playlist?list=PLUGOUZPIB0F-qv6MvKq3HGr0M_b3U2ATv)
 - [So funktioniert es](https://medium.com/better-programming/how-i-built-an-autonomous-ai-agent-for-online-research-93435a97c6c)
 - [Installation](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live-Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)
 - [Startseite](https://gptr.dev)

## Funktionen
- 📝 Erstellt Research-, Gliederungs-, Quellen- und Lern-Reports
- 📜 Kann lange und detaillierte Research-Reports erzeugen, auch mit mehr als 2.000 Wörtern
- 🌐 Aggregiert pro Recherche mehr als 20 Webquellen, um objektive und faktenbasierte Schlussfolgerungen zu ziehen
- 🖥️ Enthält eine leicht nutzbare Weboberfläche (HTML/CSS/JS)
- 🔍 Erkennt Webquellen auch mit JavaScript-Unterstützung
- 📂 Behält besuchte und verwendete Webquellen samt Kontext im Blick
- 📄 Exportiert Research-Reports als PDF, Word und mehr

Let's get started [here](/docs/gpt-researcher/getting-started/getting-started)!
