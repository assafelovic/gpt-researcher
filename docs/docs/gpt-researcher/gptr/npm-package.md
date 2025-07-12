# npm package

The [gpt-researcher npm package](https://www.npmjs.com/package/gpt-researcher) is a WebSocket client for interacting with GPT Researcher.

## Installation

```bash
npm install gpt-researcher
```

## Usage

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
