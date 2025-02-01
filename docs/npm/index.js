// index.js
const WebSocket = require('ws');

class GPTResearcherWebhook {
  constructor(options = {}) {
    this.customHost = options.host;
    this.socket = null;
    this.responseCallbacks = new Map();
  }

  getHost() {
    if (this.customHost) return this.customHost;
    
    if (typeof window !== 'undefined') {
      const { host, protocol } = window.location;
      const fullHost = host.includes('localhost') ? 
        'http://localhost:8000' : 
        `${protocol}//${host}`;
        
      return fullHost;
    }
    
    return 'http://localhost:8000'; // Default fallback
  }

  getWebSocketURI() {
    const fullHost = this.getHost();
    const host = fullHost.replace('http://', '').replace('https://', '');
    return `${fullHost.includes('https') ? 'wss:' : 'ws:'}//${host}/ws`;
  }

  async initializeWebSocket() {
    if (!this.socket) {
      const ws_uri = this.getWebSocketURI();
      this.socket = new WebSocket(ws_uri);

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket data received:', data);

        const callback = this.responseCallbacks.get('current');
        
        if (data.type === 'report') {
          if (callback && callback.onProgress) {
            callback.onProgress(data.output);
          }
        } else if (data.content === 'dev_team_result') {
          if (callback && callback.onComplete) {
            callback.onComplete(data.output);
            this.responseCallbacks.delete('current');
          }
        }
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

  async sendMessage({query, moreContext, repoName = 'assafelovic/gpt-researcher', branchName = 'master'}) {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.initializeWebSocket();
      }

      const data = {
        task: `${query}. Additional context: ${moreContext}`,
        report_type: 'research_report',
        report_source: 'web',
        tone: 'Objective',
        headers: {},
        repo_name: repoName,
        branch_name: branchName
      };

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
}

module.exports = GPTResearcherWebhook;