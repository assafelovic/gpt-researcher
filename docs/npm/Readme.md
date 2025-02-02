# GPT Researcher Webhook

The gpt-researcher npm package is a WebSocket client for interacting with GPT Researcher.

For running the gpt-researcher server, see the [Github Repo](https://github.com/assafelovic/gpt-researcher).

## Installation

```bash
npm install gpt-researcher
```

## Usage

### Basic Usage

```javascript
const GPTResearcher = require('gpt-researcher');

const researcher = new GPTResearcher({
  host: 'localhost:8000',
  logListener: (data) => console.log('logListener logging data: ',data)
});

researcher.sendMessage({
  query: 'Does providing better context reduce LLM hallucinations?',
  moreContext: 'Provide a detailed answer'
});
```


### Log Data Structure

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