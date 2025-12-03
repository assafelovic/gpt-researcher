"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import { useResearchHistory } from './useResearchHistory';
import { ResearchHistoryItem, Data, ChatMessage } from '../types/data';

// Define the shape of our context
interface ResearchHistoryContextType {
  history: ResearchHistoryItem[];
  loading: boolean;
  saveResearch: (question: string, answer: string, orderedData: Data[]) => Promise<string>;
  updateResearch: (id: string, answer: string, orderedData: Data[]) => Promise<boolean>;
  getResearchById: (id: string) => Promise<ResearchHistoryItem | null>;
  deleteResearch: (id: string) => Promise<boolean>;
  addChatMessage: (id: string, message: ChatMessage) => Promise<boolean>;
  getChatMessages: (id: string) => ChatMessage[];
  clearHistory: () => Promise<boolean>;
}

// Create the context with a default undefined value
const ResearchHistoryContext = createContext<ResearchHistoryContextType | undefined>(undefined);

// Provider component
export const ResearchHistoryProvider = ({ children }: { children: ReactNode }) => {
  // Use the hook only once here
  const researchHistory = useResearchHistory();
  
  return (
    <ResearchHistoryContext.Provider value={researchHistory}>
      {children}
    </ResearchHistoryContext.Provider>
  );
};

// Custom hook for consuming the context
export const useResearchHistoryContext = () => {
  const context = useContext(ResearchHistoryContext);
  
  if (context === undefined) {
    throw new Error('useResearchHistoryContext must be used within a ResearchHistoryProvider');
  }
  
  return context;
}; 