declare module 'gpt-researcher-ui' {
  import React from 'react';

  export interface GPTResearcherProps {
    apiUrl?: string;
    apiKey?: string;
    defaultPrompt?: string;
    onResultsChange?: (results: any) => void;
    theme?: any;
  }

  export const GPTResearcher: React.FC<GPTResearcherProps>;
}