# Embed-Skript

Mit dem Embed-Skript kannst du die neueste GPTR-NextJS-App in deine Webanwendung einbetten.

Füge dazu einfach diese zwei Script-Tags in dein HTML ein:

```javascript
<script>localStorage.setItem("GPTR_API_URL", "http://localhost:8000");</script>
<script src="https://app.gptr.dev/embed.js"></script>
```

Hier ist ein minimalistisches HTML-Beispiel. Du kannst es auch als `index.html` speichern und im Browser öffnen:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT Researcher Embed-Demo</title>
</head>
<body style="margin: 0; padding: 0;">
    <!-- GPT Researcher Embed -->
    <script>localStorage.setItem("GPTR_API_URL", "http://localhost:8000");</script>
    <script src="https://app.gptr.dev/embed.js"></script>
</body>
</html>
```

Das Beispiel nutzt einen eigenen `localStorage`-Wert für `GPTR_API_URL`. Wenn du dein eingebettetes Frontend auf einen anderen GPTR-API-Server zeigen lassen möchtest, ersetze `http://localhost:8000` einfach durch deine Serveradresse.
