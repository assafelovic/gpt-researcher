# React-Paket

Das GPTR-React-Paket ist eine Abstraktionsschicht über der NextJS-App. Damit können Nutzer das GPTR-Frontend leicht in jede React-App einbinden. Das Paket ist [auf npm verfügbar](https://www.npmjs.com/package/gpt-researcher-ui).

## Installation

```bash
npm install gpt-researcher-ui
```

## Nutzung

```javascript
import React from 'react';
import { GPTResearcher } from 'gpt-researcher-ui';

function App() {
  return (
    <div className="App">
      <GPTResearcher 
        apiUrl="http://localhost:8000"
        defaultPrompt="Was ist Quantencomputing?"
        onResultsChange={(results) => console.log('Rechercheergebnisse:', results)}
      />
    </div>
  );
}

export default App;
```

## In eine private npm-Registry veröffentlichen

Wenn du das Paket in deine eigene private npm-Registry bauen und veröffentlichen möchtest, kannst du folgende Befehle ausführen:

```bash
cd frontend/nextjs/
npm run build:lib
npm run build:types
npm publish
```
