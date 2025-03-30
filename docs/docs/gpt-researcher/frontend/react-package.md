# React Package

The GPTR React package is an abstraction on top of the NextJS app meant to empower users to easily import the GPTR frontend into any React App. The package is [available on npm](https://www.npmjs.com/package/gpt-researcher-ui).


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
        apiUrl="http://localhost:8000"
        defaultPrompt="What is quantum computing?"
        onResultsChange={(results) => console.log('Research results:', results)}
      />
    </div>
  );
}

export default App;
```


## Publishing to a private npm registry

If you'd like to build and publish the package into your own private npm registry, you can do so by running the following commands:

 ```bash
 cd frontend/nextjs/
 npm run build:lib
 npm run build:types
 npm publish
 ```
 
