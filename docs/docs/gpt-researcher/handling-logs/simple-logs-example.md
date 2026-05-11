# Einfaches Logs-Beispiel

Hier ist ein kleines Codebeispiel, das zeigt, wie du die Streaming-Logs deiner Research-Aufgaben selbst behandeln kannst.

```python
from typing import Dict, Any
import asyncio
from gpt_researcher import GPTResearcher

class CustomLogsHandler:
    """Eigener Logs-Handler für JSON-Daten."""
    def __init__(self):
        self.logs = []  # Logs zur Speicherung anlegen

    async def send_json(self, data: Dict[str, Any]) -> None:
        """JSON-Daten senden und protokollieren."""
        self.logs.append(data)  # Daten zu den Logs hinzufügen
        print(f"Mein eigener Log: {data}")  # Zur Demonstration den Log ausgeben

async def run():
    # Benötigte Parameter mit Beispielwerten definieren

    query = "Was ist bei den letzten Burning-Man-Überschwemmungen passiert?"
    report_type = "research_report"  # Zu erzeugender Report-Typ
    report_source = "online"  # Quelle, z. B. 'online' oder 'books'
    tone = "informative"  # Ton des Reports
    config_path = None  # Pfad zu einer Config-Datei, falls nötig

    # Researcher mit eigenem WebSocket-Handler initialisieren
    custom_logs_handler = CustomLogsHandler()

    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        config_path=config_path,
        websocket=custom_logs_handler
    )

    await researcher.conduct_research()  # Recherche durchführen
    report = await researcher.write_report()  # Research-Report schreiben

    return report

# Asynchrone Funktion mit asyncio starten
if __name__ == "__main__":
    asyncio.run(run())
```

Die Daten aus dem Research-Prozess werden in der Instanz `CustomLogsHandler` protokolliert und gespeichert. Du kannst das Logging-Verhalten für deine Anwendung nach Bedarf anpassen.

Beispielausgabe:

```
{
    "type": "logs",
    "content": "added_source_url",
    "output": "✅ Quellen-URL zur Recherche hinzugefügt: https://www.npr.org/2023/09/28/1202110410/how-rumors-and-conspiracy-theories-got-in-the-way-of-mauis-fire-recovery\n",
    "metadata": "https://www.npr.org/2023/09/28/1202110410/how-rumors-and-conspiracy-theories-got-in-the-way-of-mauis-fire-recovery"
}
```

Das Feld `metadata` enthält die Metadaten, die für den jeweiligen Log-Eintrag relevant sind. Lass das Skript einfach bis zum Ende laufen, um die vollständigen Logs einer Research-Aufgabe zu sehen.
