// gptr-webhook.js

const WebSocket = require('ws');

let socket = null;

function initializeWebSocket() {
  if (!socket) {
    host = 'localhost:8000'
    const ws_uri = `ws://${host}/ws`;

    socket = new WebSocket(ws_uri);

    socket.onopen = () => {
      console.log('WebSocket connection established');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket data received:', data);

      if (data.type === 'human_feedback' && data.content === 'request') {
        console.log('Human feedback requested:', data.output);
        // Handle human feedback request here
      } else {
        console.log('Received data:', data);
        // Handle other types of messages here
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

function sendWebhookMessage(message) {
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
  
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(payload);
    console.log('Message sent:', payload);
  } else {
    console.log('WebSocket is not open. Waiting for connection...');
    socket.onopen = () => {
      socket.send(payload);
      console.log('Message sent after connection:', payload);
    };
  }
}

module.exports = {
  sendWebhookMessage
};