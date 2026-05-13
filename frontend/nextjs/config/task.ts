export const task = {
  "task": {
    "query": "Befindet sich KI in einem Hype-Zyklus?",
    "include_human_feedback": false,
    "model": "gpt-4o",
    "max_sections": 3,
    "publish_formats": {
      "markdown": true,
      "pdf": true,
      "docx": true
    },
    "source": "web",
    "follow_guidelines": true,
    "guidelines": [
      "Der Bericht MUSS die ursprüngliche Frage vollständig beantworten",
      "Der Bericht MUSS im APA-Format geschrieben sein",
      "Der Bericht MUSS auf Deutsch geschrieben sein"
    ],
    "verbose": true
  },
  "initial_research": "Erste Recherchedaten hier",
  "sections": ["Abschnitt 1", "Abschnitt 2"],
  "research_data": "Recherchedaten hier",
  "title": "Forschungstitel",
  "headers": {
    "introduction": "Einleitungsüberschrift",
    "table_of_contents": "Inhaltsverzeichnis-Überschrift",
    "conclusion": "Fazit-Überschrift",
    "sources": "Quellen-Überschrift"
  },
  "date": "2023-10-01",
  "table_of_contents": "- Einleitung\n- Abschnitt 1\n- Abschnitt 2\n- Fazit",
  "introduction": "Einleitungsinhalt hier",
  "conclusion": "Fazitinhalte hier",
  "sources": ["Quelle 1", "Quelle 2"],
  "report": "Vollständiger Berichtstext hier"
}
