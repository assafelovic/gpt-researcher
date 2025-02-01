# GPT Researcher Webhook

The gpt-researcher npm package is a WebSocket client for interacting with GPT Researcher.

For running the gpt-researcher server, see the [Github Repo](https://github.com/assafelovic/gpt-researcher).

## Installation

```bash
npm install gpt-researcher
```

## Usage

```javascript
const GPTResearcherWebhook = require('gpt-researcher');

const webhook = new GPTResearcherWebhook({
  host: 'localhost:8000' // optional, defaults to this value
});

// Send a message
async function example() {
  try {
    const response = await webhook.sendMessage({
      query: 'Your research query',
      moreContext: 'Additional context'
    });
    
    console.log(response);
  } catch (error) {
    console.error(error);
  }
}

example();
```

Handling logs as they stream in:

```javascript
const GPTResearcherWebhook = require('gpt-researcher');

const researcher = new GPTResearcherWebhook({
  host: 'localhost:8000' // Optional custom host
});

async function advancedResearch() {
  try {
    const response = await researcher.sendMessage({
      query: "Analyze the impact of AI on healthcare",
      moreContext: "Focus on practical applications"
    });

    switch (response.type) {
      case 'progress':
        console.log('Research in progress:', response.data);
        break;
        
      case 'complete':
        console.log('Research completed:', response.data);
        break;
    }
  } catch (error) {
    console.error('Research failed:', error);
  }
}

advancedResearch();
```
