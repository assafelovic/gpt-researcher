// index.js
const WebSocket = require('ws');

class GPTResearcherWebhook {
  constructor(options = {}) {
    this.host = options.host || 'gpt-researcher:8000';
    this.socket = null;
    this.responseCallbacks = new Map();
    this.logListener = options.logListener; // Add this line
  }

  async initializeWebSocket() {
    if (!this.socket) {
      const ws_uri = `ws://${this.host}/ws`;
      this.socket = new WebSocket(ws_uri);

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Handle logs with custom listener if provided
        if (this.logListener) {
          this.logListener(data);
        } else {
          console.log('WebSocket data received:', data);
        }

        const callback = this.responseCallbacks.get('current');
        
      };

      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
        this.socket = null;
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    }
  }

  async sendMessage({query, moreContext, useHTPP = false, execute_in_background = true, repoName = 'assafelovic/gpt-researcher', branchName = 'master'}) {
    const data = {
      task: `${query}. Additional context: ${moreContext}`,
      report_type: 'research_report',
      report_source: 'web',
      tone: 'Objective',
      headers: {},
      repo_name: repoName,
      branch_name: branchName,
      execute_in_background: execute_in_background
    };

    if (useHTPP) {
      return await this.sendHttpRequest(data);
    } else {
      return await this.sendWebSocketRequest(data);
    }
  }

  async sendHttpRequest(data) {
    try {
      const response = await axios.post(`http://${this.host}/report/`, data);
      return { message: 'success', data: response.data };
    } catch (error) {
      console.error('HTTP request error:', error);
      return { message: 'error', error: error.message };
    }
  }

  async sendWebSocketRequest() {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.initializeWebSocket();
      }

      const payload = "start " + JSON.stringify(data);

      this.responseCallbacks.set('current', {
        onProgress: (progressData) => {
          resolve({ type: 'progress', data: progressData });
        },
        onComplete: (finalData) => {
          resolve({ type: 'complete', data: finalData });
        }
      });

      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(payload);
        console.log('Message sent:', payload);
      } else {
        this.socket.onopen = () => {
          this.socket.send(payload);
          console.log('Message sent after connection:', payload);
        };
      }
    });
  }

  async getReport(reportId) {
    try {
      const response = await axios.get(`http://${this.host}/report/${reportId}`);
      return response;
    } catch (error) {
      console.error('HTTP request error:', error);
      return { message: 'error', error: error.message };
    }
  }
}

module.exports = GPTResearcherWebhook;