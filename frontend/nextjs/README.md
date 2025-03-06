# GPT Researcher UI

A React component library for integrating the GPT Researcher interface into your React applications. Take it for a test ride with the [GPTR React Starter Template](https://github.com/elishakay/gpt-researcher-react), or simply:

## Installation

```bash
npm install gpt-researcher-ui
```

## Usage

```javascript
import React from 'react';
import { GPTResearcher } from 'gpt-researcher-ui';

function App() {
  return (
    <div className="App">
      <GPTResearcher 
        apiUrl="http://your-gpt-researcher-backend.com" 
        apiKey="your-api-key-if-needed"
        defaultPrompt="What is quantum computing?"
        onResultsChange={(results) => console.log('Research results:', results)}
      />
    </div>
  );
}

export default App;
```

## Advanced Usage

```javascript
import React, { useState } from 'react';
import { GPTResearcher } from 'gpt-researcher-ui';

function App() {
  const [results, setResults] = useState([]);

  const handleResultsChange = (newResults) => {
    setResults(newResults);
    console.log('Research progress:', newResults);
  };

  return (
    <div className="App">
      <h1>My Research Application</h1>
      
      <GPTResearcher 
        apiUrl="http://localhost:8000"
        apiKey="your-api-key-if-needed"
        defaultPrompt="Explain the impact of quantum computing on cryptography"
        onResultsChange={handleResultsChange}
      />
      
      {/* You can use the results state elsewhere in your app */}
      <div className="results-summary">
        {results.length > 0 && (
          <p>Research in progress: {results.length} items processed</p>
        )}
      </div>
    </div>
  );
}

export default App;
```