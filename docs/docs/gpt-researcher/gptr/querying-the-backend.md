# Backend abfragen

## Einführung

In diesem Abschnitt zeigen wir, wie du den GPTR-Backend-Server abfragst. Der GPTR-Backend-Server ist ein Python-Server, der das GPTR-Python-Paket ausführt. Er lauscht auf WebSocket-Verbindungen und verarbeitet eingehende Nachrichten, um Reports zu erzeugen und Logs sowie Ergebnisse an den Client zurückzustreamen.

> Hinweis zum Fork: Der validierte lokale Stack dieses Repos verwendet `localhost:8002` für die Backend-API. Das folgende Upstream-Beispiel nutzt weiterhin den ursprünglichen Wert `localhost:8000`, also ersetze ihn, wenn du dem fork-spezifischen Setup folgst.

Ein Beispiel für einen WebSocket-Client ist in der folgenden Datei `gptr-webhook.js` implementiert.

Diese Funktion sendet eine Webhook-Nachricht an das GPTR-Python-Backend auf `localhost:8000`. Das Beispiel lässt sich aber auch anpassen, um einen [auf Linux gehosteten GPTR-Server](https://docs.gptr.dev/docs/gpt-researcher/getting-started/linux-deployment) abzufragen.

// gptr-webhook.js

```javascript

const WebSocket = require('ws');

let socket = null;
let responseCallback = null;

async function initializeWebSocket() {
  if (!socket) {
    const host = 'localhost:8000';
    const ws_uri = `ws://${host}/ws`;

    socket = new WebSocket(ws_uri);

    socket.onopen = () => {
      console.log('WebSocket-Verbindung hergestellt');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket-Daten empfangen:', data);

      if (data.content === 'dev_team_result' 
          && data.output.rubber_ducker_thoughts != undefined
          && data.output.tech_lead_review != undefined) {
        if (responseCallback) {
          responseCallback(data.output);
          responseCallback = null; // Callback danach löschen
        }
      } else {
        console.log('Daten empfangen:', data);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket-Verbindung geschlossen');
      socket = null;
    };

    socket.onerror = (error) => {
      console.error('WebSocket-Fehler:', error);
    };
  }
}

async function sendWebhookMessage(message) {
  return new Promise((resolve, reject) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      initializeWebSocket();
    }

    const data = {
      task: message,
      report_type: 'dev_team',
      report_source: 'web',
      tone: 'Objective',
      headers: {},
      repo_name: 'elishakay/gpt-researcher'
    };

    const payload = "start " + JSON.stringify(data);

    responseCallback = (response) => {
      resolve(response); // Promise mit der WebSocket-Antwort auflösen
    };

    if (socket.readyState === WebSocket.OPEN) {
      socket.send(payload);
      console.log('Nachricht gesendet:', payload);
    } else {
      socket.onopen = () => {
        socket.send(payload);
        console.log('Nachricht nach Verbindungsaufbau gesendet:', payload);
      };
    }
  });
}

module.exports = {
  sendWebhookMessage
};
```

Und so kannst du diese Hilfsfunktion verwenden:

```javascript
const { sendWebhookMessage } = require('./gptr-webhook');

async function main() {
  const message = 'How do I get started with GPT-Researcher Websockets?';
  const response = await sendWebhookMessage(message);
  console.log('Response:', response);
}
```
