// gptr-webhook.js
const WebSocket = require('ws');

let socket = null;
const responseCallbacks = new Map(); // Using Map for multiple callbacks

async function initializeWebSocket() {
  if (!socket) {
    const host = 'gpt-researcher:8000';
    const ws_uri = `ws://${host}/ws`;

    socket = new WebSocket(ws_uri);

    socket.onopen = () => {
      console.log('WebSocket connection established');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket data received:', data);

      // Get the callback for this request
      const callback = responseCallbacks.get('current');
      
      if (data.type === 'report') {
        // Send progress updates
        if (callback && callback.onProgress) {
          callback.onProgress(data.output);
        }
      } else if (data.content === 'dev_team_result') {
        // Send final result
        if (callback && callback.onComplete) {
          callback.onComplete(data.output);
          responseCallbacks.delete('current'); // Clean up after completion
        }
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

async function sendWebhookMessage({query, moreContext}) {
  return new Promise((resolve, reject) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      initializeWebSocket();
    }

    const data = {
      task: `${query}. Additional context: ${moreContext}`,
      report_type: 'research_report',
      report_source: 'web',
      tone: 'Objective',
      headers: {},
      repo_name: typeof repoName === 'undefined' || repoName === '' ? 'assafelovic/gpt-researcher' : repoName,
      branch_name: typeof branchName === 'undefined' || branchName === '' ? 'master' : branchName
    };

    const payload = "start " + JSON.stringify(data);

    // Store both progress and completion callbacks
    responseCallbacks.set('current', {
      onProgress: (progressData) => {
        resolve({ type: 'progress', data: progressData });
      },
      onComplete: (finalData) => {
        resolve({ type: 'complete', data: finalData });
      }
    });

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