// index.js
const WebSocket = require('ws');

class GPTResearcher {
  constructor(options = {}) {
    this.host = options.host || 'http://localhost:8000';
    this.socket = null;
    this.responseCallbacks = new Map();
    this.logListener = options.logListener;
    this.tone = options.tone || 'Reflective';
  }

  async initializeWebSocket() {
    if (!this.socket) {      
      const protocol = this.host.includes('https') ? 'wss:' : 'ws:';
      const cleanHost = this.host.replace('http://', '').replace('https://', '');
      const ws_uri = `${protocol}//${cleanHost}/ws`;

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

  async sendMessage({
    task,
    useHTTP = false,
    reportType = 'research_report',
    reportSource = 'web', 
    queryDomains = [],
    tone = 'Reflective',
    query,
    moreContext
  }) {
    const data = {
      task: query ? `${query}. Additional context: ${moreContext}` : task,
      report_type: reportType,
      report_source: reportSource,
      headers: {},
      tone: tone,
      query_domains: queryDomains
    };

    if (useHTTP) {
      return this.sendHttpRequest(data);
    }

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

  async sendHttpRequest(data) {
    try {
      const response = await axios.post(`${this.host}/report/`, data);
      return { message: 'success', data: response.data };
    } catch (error) {
      console.error('HTTP request error:', error);
      return { message: 'error', error: error.message };
    }
  }

  async getReport(reportId) {
    try {
      const response = await axios.get(`${this.host}/report/${reportId}`);
      return response;
    } catch (error) {
      console.error('HTTP request error:', error);
      return { message: 'error', error: error.message };
    }
  }
}

module.exports = GPTResearcher;