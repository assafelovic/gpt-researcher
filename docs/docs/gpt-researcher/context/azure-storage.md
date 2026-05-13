# Azure Storage

Wenn du Azure Blob Storage als Quelle für den Kontext deines GPT-Researcher-Reports nutzen möchtest, gehe so vor:

> **Schritt 1** - Setze diese Umgebungsvariablen in einer `.env`-Datei im Projektstamm

```bash
AZURE_CONNECTION_STRING=
AZURE_CONTAINER_NAME=
```

> **Schritt 2** - Füge die Abhängigkeit `azure-storage-blob` zu deiner `requirements.txt` hinzu

```bash
azure-storage-blob
```

> **Schritt 3** - Wenn du die `GPTResearcher`-Klasse aufrufst, übergib `report_source="azure"`

```python
report = GPTResearcher(
    query="Was ist bei den letzten Burning-Man-Überschwemmungen passiert?",
    report_type="research_report",
    report_source="azure",
)
```
