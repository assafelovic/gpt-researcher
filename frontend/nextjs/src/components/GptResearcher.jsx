// frontend/nextjs/src/components/GptResearcher.jsx
import React, { useState } from 'react';
import { ChakraProvider } from '@chakra-ui/react';
// Import components
import ResearchForm from '../../components/Task/ResearchForm';
import { ResearchResults } from '../../components/ResearchResults';

// Configuration options interface
export interface GptResearcherConfig {
  apiUrl?: string;
  apiKey?: string;
  defaultQuery?: string;
  theme?: object;
}

const GptResearcher = ({ 
  apiUrl = process.env.NEXT_PUBLIC_GPTR_API_URL || 'http://localhost:8000',
  apiKey = '',
  defaultQuery = '',
  theme = {} 
}: GptResearcherConfig) => {
  const [results, setResults] = useState(null);
  
  // Your existing logic for handling research
  
  return (
    <ChakraProvider theme={theme}>
      <div className="gpt-researcher-container">
        {!results ? (
          <ResearchForm 
            onSubmit={handleSubmit} 
            defaultQuery={defaultQuery}
          />
        ) : (
          <ResearchResults results={results} />
        )}
      </div>
    </ChakraProvider>
  );
};

export default GptResearcher;