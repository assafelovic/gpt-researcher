# npm-Paket

Das [gpt-researcher npm-Paket](https://www.npmjs.com/package/gpt-researcher) ist ein WebSocket-Client für die Kommunikation mit GPT Researcher.

## Installation

```bash
npm install gpt-researcher
```

## Nutzung

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
