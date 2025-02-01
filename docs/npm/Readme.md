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

## Usage with Log Listener

```javascript
const GPTResearcherWebhook = require('gpt-researcher');

// Create a custom log listener
const logListener = (logData) => {
  const { type, content, output, metadata } = logData;
  
  switch (content) {
    case 'added_source_url':
      console.log('New source added:', metadata);
      break;
    case 'scraping_content':
      console.log('Scraping progress:', output);
      break;
    case 'researching':
      console.log('Research status:', output);
      break;
    // ... handle other log types as needed
    default:
      console.log('Log received:', logData);
  }
};

// Initialize webhook with custom log listener
const researcher = new GPTResearcherWebhook({
  host: 'gpt-researcher:8000', // optional
  logListener: logListener     // add your custom listener
});

// Example usage
async function runResearch() {
  try {
    const response = await researcher.sendMessage({
      query: 'What are the latest developments in AI?',
      moreContext: 'Focus on 2024'
    });
    
    if (response.type === 'progress') {
      console.log('Progress update:', response.data);
    } else if (response.type === 'complete') {
      console.log('Research complete:', response.data);
    }
  } catch (error) {
    console.error('Research error:', error);
  }
}

runResearch();
```


Log Data Structure

The `logListener` function receives log data with this structure:

```javascript
{
  type: 'logs',
  content: string,    // e.g., 'added_source_url', 'researching', 'scraping_content'
  output: string,     // Human-readable output message
  metadata: any       // Additional data (URLs, counts, etc.)
}
```

Common log content types:

```javascript
'added_source_url': New source URL added
'researching': Research status updates
'scraping_urls': Starting URL scraping
'scraping_content': Content scraping progress
'scraping_images': Image processing updates
'scraping_complete': Scraping completion
'fetching_query_content': Query processing
```