# Automatisierte Tests

## Automatisiertes Testen mit GitHub Actions

Dieses Repository enthält den Code für automatisierte Tests des GPT-Researcher-Repos über GitHub Actions.

Die Tests laufen in einem Docker-Container und werden dort über das `pytest`-Modul ausgeführt.

## Tests ausführen

Du kannst die Tests so starten:

### Per Docker-Befehl

```bash
docker-compose --profile test run --rm gpt-researcher-tests
```

### Über eine GitHub Action

![image](https://github.com/user-attachments/assets/721fca20-01bb-4c10-9cf9-19d823bebbb0)

Hier die nötigen Repo-Einstellungen und Screenshots:

Schritt 1: Öffne im Repository den Tab **Settings**

Schritt 2: Erstelle eine neue Umgebung mit dem Namen **tests** (alles klein geschrieben)

Schritt 3: Öffne die **tests**-Umgebung und hinterlege die Secrets `OPENAI_API_KEY` und `TAVILY_API_KEY`

Die Keys findest du hier:

https://app.tavily.com/sign-in

https://platform.openai.com/api-keys

![Screen Shot 2024-07-28 at 9 00 19](https://github.com/user-attachments/assets/7cd341c6-d8d4-461f-ab5e-325abc9fe509)
![Screen Shot 2024-07-28 at 9 02 55](https://github.com/user-attachments/assets/a3744f01-06a6-4c9d-8aa0-1fc742d3e866)

Wenn alles korrekt konfiguriert ist, sollte der GitHub Action-Status beim Erstellen eines neuen PRs oder beim Pushen auf einen offenen PR so aussehen:

![Screen Shot 2024-07-28 at 8 57 02](https://github.com/user-attachments/assets/30dbc668-4e6a-4b3b-a02e-dc859fc9bd3d)
