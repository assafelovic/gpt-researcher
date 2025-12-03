import React, { useRef, useState } from "react";
import { Toaster } from "react-hot-toast";
import Image from "next/image";
import { ChatBoxSettings } from "@/types/data";
import { useResearchHistoryContext } from "@/hooks/ResearchHistoryContext";
import { formatDistanceToNow } from "date-fns";

interface MobileLayoutProps {
  children: React.ReactNode;
  loading: boolean;
  isStopped: boolean;
  showResult: boolean;
  onStop?: () => void;
  onNewResearch?: () => void;
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  mainContentRef?: React.RefObject<HTMLDivElement>;
  toastOptions?: Record<string, any>;
  toggleSidebar?: () => void;
}

export default function MobileLayout({
  children,
  loading,
  isStopped,
  showResult,
  onStop,
  onNewResearch,
  chatBoxSettings,
  setChatBoxSettings,
  mainContentRef,
  toastOptions = {},
  toggleSidebar
}: MobileLayoutProps) {
  const defaultRef = useRef<HTMLDivElement>(null);
  const contentRef = mainContentRef || defaultRef;
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  
  // Get research history from context
  const { history } = useResearchHistoryContext();
  
  // Format timestamp for display
  const formatTimestamp = (timestamp: number | string | Date | undefined) => {
    if (!timestamp) return 'Unknown time';
    
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return 'Unknown time';
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return 'Unknown time';
    }
  };
  
  // Handle history item selection
  const handleHistoryItemClick = (id: string) => {
    setShowHistory(false);
    window.location.href = `/research/${id}`;
  };
  
  return (
    <main className="flex flex-col min-h-screen bg-gray-900">
      <Toaster 
        position="bottom-center" 
        toastOptions={toastOptions}
      />
      
      {/* Mobile Header - simplified and compact */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/95 backdrop-blur-md border-b border-gray-800/50 shadow-md">
        <div className="flex items-center justify-between px-4 h-14">
          {/* Logo */}
          <div className="flex items-center">
            <a href="/" className="flex items-center">
              <img
                src="/img/gptr-logo.png"
                alt="GPT Researcher"
                width={30}
                height={30}
                className="rounded-md mr-2"
              />
              <span className="font-medium text-gray-200 text-sm">GPT Researcher</span>
            </a>
          </div>
          
          {/* Actions */}
          <div className="flex items-center space-x-2">
            {loading && (
              <button
                onClick={onStop}
                className="p-2 rounded-full bg-red-500/20 text-red-300 hover:bg-red-500/30"
                aria-label="Stop research"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>
                </svg>
              </button>
            )}
            
            {showResult && onNewResearch && (
              <button
                onClick={onNewResearch}
                className="p-2 rounded-full bg-sky-500/20 text-sky-300 hover:bg-sky-500/30"
                aria-label="New research"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
            )}
            
            <button
              onClick={() => {
                setShowHistory(!showHistory);
                setShowSettings(false);
                if (toggleSidebar) toggleSidebar();
              }}
              className="p-2 rounded-full bg-gray-800/50 text-gray-300 hover:bg-gray-700/50"
              aria-label="View history"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </button>
            
            <button
              onClick={() => {
                setShowSettings(!showSettings);
                setShowHistory(false);
              }}
              className="p-2 rounded-full bg-gray-800/50 text-gray-300 hover:bg-gray-700/50"
              aria-label="Settings"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
          </div>
        </div>
        
        {/* History panel - slides down when active */}
        {showHistory && (
          <div className="px-4 py-3 bg-gray-800/90 border-t border-gray-700/50 animate-slide-down shadow-lg max-h-[70vh] overflow-y-auto custom-scrollbar">
            <div className="mb-3 flex justify-between items-center">
              <h3 className="text-sm font-medium text-gray-200">Research History</h3>
              <button 
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            {history.length > 0 ? (
              <div className="space-y-2">
                {history.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleHistoryItemClick(item.id)}
                    className="w-full bg-gray-900/60 hover:bg-gray-800 rounded-lg p-3 text-left transition-colors focus:outline-none focus:ring-1 focus:ring-teal-500/50 border border-gray-700/30"
                  >
                    <h3 className="text-sm font-medium text-gray-200 line-clamp-1">{item.question}</h3>
                    <p className="text-xs text-gray-400 mt-1.5 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatTimestamp(item.timestamp || (item as any).updated_at || (item as any).created_at)}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-700/50 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <p className="text-sm text-gray-400">No research history yet</p>
                <button 
                  onClick={onNewResearch} 
                  className="mt-3 px-4 py-2 text-xs text-teal-300 bg-teal-900/30 hover:bg-teal-800/40 rounded-md transition-colors"
                >
                  Start New Research
                </button>
              </div>
            )}
            
            {history.length > 0 && (
              <div className="mt-3 pt-2 border-t border-gray-700/30 flex justify-center">
                <a 
                  href="/history" 
                  className="text-xs text-teal-400 hover:text-teal-300 transition-colors"
                >
                  View All Research History
                </a>
              </div>
            )}
          </div>
        )}
        
        {/* Settings panel - slides down when active */}
        {showSettings && (
          <div className="px-4 py-3 bg-gray-800/90 border-t border-gray-700/50 animate-slide-down shadow-lg">
            <div className="mb-2 flex justify-between items-center">
              <h3 className="text-sm font-medium text-gray-200">Settings</h3>
              <button 
                onClick={() => setShowSettings(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Report Type</label>
                <select 
                  className="w-full bg-gray-900 border border-gray-700 rounded-md py-1.5 px-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:border-teal-500"
                  value={chatBoxSettings.report_type}
                  onChange={(e) => setChatBoxSettings({...chatBoxSettings, report_type: e.target.value})}
                >
                  <option value="research_report">Summary - Short and fast (~2 min)</option>
                  <option value="deep">Deep Research Report</option>
                  <option value="multi_agents">Multi Agents Report</option>
                  <option value="detailed_report">Detailed - In depth and longer (~5 min)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs text-gray-400 mb-1">Research Source</label>
                <select 
                  className="w-full bg-gray-900 border border-gray-700 rounded-md py-1.5 px-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:border-teal-500"
                  value={chatBoxSettings.report_source}
                  onChange={(e) => setChatBoxSettings({...chatBoxSettings, report_source: e.target.value})}
                >
                  <option value="web">Web</option>
                  <option value="scholar">Scholar</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs text-gray-400 mb-1">Research Tone</label>
                <select 
                  className="w-full bg-gray-900 border border-gray-700 rounded-md py-1.5 px-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:border-teal-500"
                  value={chatBoxSettings.tone}
                  onChange={(e) => setChatBoxSettings({...chatBoxSettings, tone: e.target.value})}
                >
                  <option value="Objective">Objective - Impartial and unbiased presentation of facts</option>
                  <option value="Formal">Formal - Adheres to academic standards</option>
                  <option value="Analytical">Analytical - Critical evaluation of data</option>
                  <option value="Persuasive">Persuasive - Convincing viewpoint</option>
                  <option value="Informative">Informative - Clear, comprehensive information</option>
                  <option value="Simple">Simple - Basic vocabulary and clear explanations</option>
                  <option value="Casual">Casual - Conversational style</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs text-gray-400 mb-1">Layout</label>
                <select 
                  className="w-full bg-gray-900 border border-gray-700 rounded-md py-1.5 px-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:border-teal-500"
                  value={chatBoxSettings.layoutType}
                  onChange={(e) => setChatBoxSettings({...chatBoxSettings, layoutType: e.target.value})}
                >
                  <option value="copilot">Copilot - Chat style layout</option>
                  <option value="document">Document - Traditional report layout</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </header>
      
      {/* Main content area */}
      <div 
        ref={contentRef}
        className="flex-1 pt-14" /* Matches header height */
      >
        {children}
      </div>
      
      {/* Footer */}
      <footer className="mt-auto py-3 px-4 text-center border-t border-gray-800/40 bg-gray-900/80 backdrop-blur-sm">
        <div className="flex items-center justify-center gap-5 mb-3">
          <a href="https://gptr.dev" target="_blank" className="text-gray-400 hover:text-teal-400 transition-colors">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="w-5 h-5"
            >
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </a>
          <a href="https://github.com/assafelovic/gpt-researcher" target="_blank" className="text-gray-400 hover:text-gray-300 transition-colors">
            <img
              src="/img/github.svg"
              alt="GitHub"
              width={20}
              height={20}
              className="w-5 h-5"
            />
          </a>
          <a href="https://discord.gg/QgZXvJAccX" target="_blank" className="text-gray-400 hover:text-gray-300 transition-colors">
            <img
              src="/img/discord.svg"
              alt="Discord"
              width={20}
              height={20}
              className="w-5 h-5"
            />
          </a>
          <a href="https://hub.docker.com/r/gptresearcher/gpt-researcher" target="_blank" className="text-gray-400 hover:text-gray-300 transition-colors">
            <img
              src="/img/docker.svg"
              alt="Docker"
              width={20}
              height={20}
              className="w-5 h-5"
            />
          </a>
        </div>
        <div className="text-xs text-gray-400">
          © {new Date().getFullYear()} GPT Researcher. All rights reserved.
        </div>
      </footer>
      
      {/* Custom animations */}
      <style jsx global>{`
        .animate-slide-down {
          animation: slideDown 0.3s ease-out forwards;
        }
        
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        /* Custom scrollbar for history panel */
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(17, 24, 39, 0.1);
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(75, 85, 99, 0.5);
          border-radius: 20px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(75, 85, 99, 0.7);
        }
        
        .line-clamp-1 {
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
        }
        
        @media (display-mode: standalone) {
          /* PWA specific styles */
          body {
            overscroll-behavior-y: contain;
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            user-select: none;
          }
        }
      `}</style>
    </main>
  );
} 