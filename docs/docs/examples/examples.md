# Einfacher Lauf

## PIP-Paket ausführen

```python
from gpt_researcher import GPTResearcher
import asyncio

async def main():
    """
    Dieses Beispiel zeigt, wie ein Research-Report ausgeführt wird.
    """
    query = "Was ist bei den letzten Burning-Man-Überschwemmungen passiert?"
    report_type = "research_report"

    researcher = GPTResearcher(query=query, report_type=report_type, config_path=None)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

if __name__ == "__main__":
    asyncio.run(main())
```

## Benutzerdefiniertes Report-Format

```python
from gpt_researcher import GPTResearcher
import asyncio

async def main():
    """
    Dieses Beispiel zeigt, wie du eigene Prompts zur Formatsteuerung des Reports nutzt.
    """
    query = "Was sind die neuesten Fortschritte bei erneuerbaren Energien?"
    report_type = "research_report"

    researcher = GPTResearcher(query=query, report_type=report_type)
    await researcher.conduct_research()

    standard_report = await researcher.write_report()
    print("Standard-Report erzeugt")

    custom_prompt = "Gib eine knappe Zusammenfassung in 2 Absätzen ohne Zitate."
    short_report = await researcher.write_report(custom_prompt=custom_prompt)
    print("Kurzer Report erzeugt")

    bullet_prompt = "Liste die 5 wichtigsten Fortschritte als Stichpunkte mit kurzen Erklärungen auf."
    bullet_report = await researcher.write_report(custom_prompt=bullet_prompt)
    print("Bullet-Point-Report erzeugt")

    return standard_report, short_report, bullet_report

if __name__ == "__main__":
    asyncio.run(main())
```

Weitere Beispiele für eigene Prompts findest du in der Datei `custom_prompt.py` im Beispiele-Verzeichnis.
