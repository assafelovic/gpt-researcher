import { useState, useEffect } from 'react';
import { ResearchHistoryItem, Data } from '../types/data';

export const useResearchHistory = () => {
  const [history, setHistory] = useState<ResearchHistoryItem[]>([]);
  
  // Load history from localStorage on initial render
  useEffect(() => {
    const storedHistory = localStorage.getItem('researchHistory');
    if (storedHistory) {
      try {
        setHistory(JSON.parse(storedHistory));
      } catch (error) {
        console.error('Error parsing research history:', error);
        // If there's an error parsing, reset the history
        localStorage.removeItem('researchHistory');
      }
    }
  }, []);

  // Save research to history
  const saveResearch = (question: string, answer: string, orderedData: Data[]) => {
    const newItem: ResearchHistoryItem = {
      id: Date.now().toString(),
      question,
      answer,
      timestamp: Date.now(),
      orderedData,
    };

    const updatedHistory = [newItem, ...history];
    setHistory(updatedHistory);
    localStorage.setItem('researchHistory', JSON.stringify(updatedHistory));
    return newItem.id;
  };

  // Get a specific research item by ID
  const getResearchById = (id: string) => {
    return history.find(item => item.id === id);
  };

  // Delete a research item
  const deleteResearch = (id: string) => {
    const updatedHistory = history.filter(item => item.id !== id);
    setHistory(updatedHistory);
    localStorage.setItem('researchHistory', JSON.stringify(updatedHistory));
  };

  // Clear all history
  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('researchHistory');
  };

  return {
    history,
    saveResearch,
    getResearchById,
    deleteResearch,
    clearHistory,
  };
}; 