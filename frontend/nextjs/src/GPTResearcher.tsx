// src/GPTResearcher.tsx
import React, { useState } from 'react';

export interface GPTResearcherProps {
  apiUrl?: string;
  apiKey?: string;
  defaultPrompt?: string;
  onResultsChange?: (results: any) => void;
  theme?: any;
}

export const GPTResearcher: React.FC<GPTResearcherProps> = ({
  apiUrl = 'http://localhost:8000',
  apiKey = '',
  defaultPrompt = '',
  onResultsChange,
  theme = {}
}) => {
  const [promptValue, setPromptValue] = useState(defaultPrompt);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = async () => {
    if (!promptValue.trim()) return;
    
    setLoading(true);
    
    try {
      // Basic implementation that connects to the backend
      const response = await fetch(`${apiUrl}/api/research`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {})
        },
        body: JSON.stringify({ query: promptValue })
      });
      
      const data = await response.json();
      setResults([data]);
      
      if (onResultsChange) {
        onResultsChange([data]);
      }
    } catch (error) {
      console.error('Error performing research:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gpt-researcher-container" style={theme.container}>
      <div className="gpt-researcher-header" style={theme.header}>
        <h1>GPT Researcher</h1>
      </div>
      
      <div className="gpt-researcher-input" style={theme.inputArea}>
        <input
          type="text"
          value={promptValue}
          onChange={(e) => setPromptValue(e.target.value)}
          placeholder="Enter your research question..."
          style={theme.input}
        />
        <button 
          onClick={handleSearch}
          disabled={loading}
          style={theme.button}
        >
          {loading ? 'Researching...' : 'Research'}
        </button>
      </div>
      
      <div className="gpt-researcher-results" style={theme.results}>
        {results.length > 0 ? (
          <div>
            <h2>Research Results</h2>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </div>
        ) : (
          <p>Enter a question above to start researching</p>
        )}
      </div>
    </div>
  );
};