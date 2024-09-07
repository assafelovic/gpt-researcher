# Querying the Backend

## Introduction

In this section, we will discuss how to query the GPTR backend server. The GPTR backend server is a Python server that runs the GPTR Python package. The server listens for WebSocket connections and processes incoming messages to generate reports, streaming back logs and results to the client.

An example WebSocket client is implemented in the `gptr-webhook.js` file below.

This function sends a Webhook Message to the GPTR Python backend running on localhost:8000, but this example can also be modified to query a [GPTR Server hosted on Linux](https://docs.gptr.dev/docs/gpt-researcher/getting-started/linux-deployment).

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
      console.log('WebSocket connection established');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket data received:', data);

      if (data.content === 'dev_team_result' 
          && data.output.rubber_ducker_thoughts != undefined
          && data.output.tech_lead_review != undefined) {
        if (responseCallback) {
          responseCallback(data.output);
          responseCallback = null; // Clear callback after use
        }
      } else {
        console.log('Received data:', data);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
      socket = null;
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
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
      resolve(response); // Resolve the promise with the WebSocket response
    };

    if (socket.readyState === WebSocket.OPEN) {
      socket.send(payload);
      console.log('Message sent:', payload);
    } else {
      socket.onopen = () => {
        socket.send(payload);
        console.log('Message sent after connection:', payload);
      };
    }
  });
}

module.exports = {
  sendWebhookMessage
};
```

And here's how you can leverage this helper function:

```javascript
const { sendWebhookMessage } = require('./gptr-webhook');

async function main() {
  const message = 'How do I get started with GPT-Researcher Websockets?';
  const response = await sendWebhookMessage(message);
  console.log('Response:', response);
}
```