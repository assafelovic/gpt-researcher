import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ResearchHistoryItem } from '../types/data';
import { formatDistanceToNow } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';

interface ResearchSidebarProps {
  history: ResearchHistoryItem[];
  onSelectResearch: (id: string) => void;
  onNewResearch: () => void;
  onDeleteResearch: (id: string) => void;
  isOpen: boolean;
  toggleSidebar: () => void;
}

const ResearchSidebar: React.FC<ResearchSidebarProps> = ({
  history,
  onSelectResearch,
  onNewResearch,
  onDeleteResearch,
  isOpen,
  toggleSidebar,
}) => {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && 
          sidebarRef.current && 
          !sidebarRef.current.contains(event.target as Node)) {
        toggleSidebar();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, toggleSidebar]);

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

  // Animation variants
  const sidebarVariants = {
    open: { 
      width: 'var(--sidebar-width)', 
      transition: { type: 'spring', stiffness: 250, damping: 25 } 
    },
    closed: { 
      width: 'var(--sidebar-min-width)', 
      transition: { type: 'spring', stiffness: 250, damping: 25, delay: 0.1 } 
    }
  };
  
  const fadeInVariants = {
    hidden: { opacity: 0, transition: { duration: 0.2 } },
    visible: { opacity: 1, transition: { duration: 0.3 } }
  };

  return (
    <>
      {/* Overlay for mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="sidebar-overlay md:hidden fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40" 
            onClick={toggleSidebar}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>
      
      <motion.div 
        ref={sidebarRef} 
        className="fixed top-0 left-0 h-full sidebar-z-index"
        variants={sidebarVariants}
        initial={false}
        animate={isOpen ? 'open' : 'closed'}
        style={{
          '--sidebar-width': 'min(300px, 85vw)',
          '--sidebar-min-width': '12px'
        } as React.CSSProperties}
      >
        {/* Sidebar content */}
        <div 
          className={`h-full transition-all duration-300 text-white overflow-hidden 
            ${isOpen 
              ? 'bg-gray-900/80 backdrop-blur-md shadow-2xl shadow-black/30 p-3 sm:p-4' 
              : 'bg-transparent p-0'
            }`}
        >
          {/* Toggle button - only shown when sidebar is closed */}
          <AnimatePresence mode="wait">
            {!isOpen ? (
              <motion.div
                key="toggle-button"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="absolute left-4 sm:left-6 mx-auto top-1.5 sm:top-3.5 w-8 sm:w-10 h-8 sm:h-10 flex items-center justify-center rounded-full shadow-sm z-10 overflow-hidden cursor-pointer group"
                onClick={toggleSidebar}
                aria-label="Open sidebar"
              >
                {/* Subtle glowing background */}
                <div className="absolute inset-0 bg-gradient-to-br from-teal-500/15 via-cyan-400/12 to-blue-500/10 group-hover:from-teal-500/25 group-hover:via-cyan-400/20 group-hover:to-blue-500/15 transition-all duration-300 group-hover:shadow-[0_0_15px_rgba(20,184,166,0.3)]"></div>
                
                {/* Icon with subtle glow effect */}
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-5 sm:h-6 w-5 sm:w-6 relative text-teal-100/90 filter drop-shadow-[0_0_1px_rgba(45,212,191,0.5)]" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </motion.div>
            ) : (
              <motion.div
                key="sidebar-content"
                initial="hidden"
                animate="visible"
                exit="hidden"
                variants={fadeInVariants}
              >
                <div className="flex justify-between items-center mb-5 sm:mb-6">
                  <h2 className="text-lg sm:text-xl font-semibold bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">Research History</h2>
                  <button
                    onClick={toggleSidebar}
                    className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center bg-gray-800/60 text-white rounded-full shadow-lg hover:bg-gray-800 transition-all duration-300 group"
                    aria-label="Close sidebar"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                </div>

                {/* New Research button */}
                <button
                  onClick={onNewResearch}
                  className="relative w-full py-2.5 sm:py-3 px-3 sm:px-4 mb-5 sm:mb-6 bg-teal-500 text-white rounded-md font-bold text-sm transition-all duration-300 overflow-hidden group"
                >
                  {/* Gradient background on hover */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-gradient-to-br from-[#0cdbb6] via-[#1fd0f0] to-[#06dbee] transition-opacity duration-500"></div>
                  
                  {/* Magical glow effect */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" 
                      style={{
                        boxShadow: 'inset 0 0 20px 5px rgba(255, 255, 255, 0.2)',
                        background: 'radial-gradient(circle at center, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0) 70%)'
                      }}>
                  </div>
                  
                  <div className="relative z-10 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 sm:h-5 w-4 sm:w-5 mr-2 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Research
                  </div>
                </button>

                {/* History list with improved scrollbar */}
                <div className="overflow-y-auto h-[calc(100vh-150px)] sm:h-[calc(100vh-190px)] pr-1 custom-scrollbar">
                  {history.length === 0 ? (
                    <div className="text-center py-8 sm:py-10 px-4">
                      <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-gray-800/60 to-gray-700/40 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 sm:h-10 w-8 sm:w-10 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-300 mb-2">No research history yet</h3>
                      <p className="text-sm text-gray-400">Start your first research journey to build your knowledge library</p>
                    </div>
                  ) : (
                    <ul className="space-y-2 sm:space-y-3">
                      {history.map((item) => (
                        <motion.li 
                          key={item.id}
                          className="relative rounded-xl transition-all duration-300 overflow-hidden group bg-gray-900/40 hover:bg-gray-800/60 border border-gray-700/30 hover:border-gray-600/50 backdrop-blur-sm"
                          onMouseEnter={() => setHoveredItem(item.id)}
                          onMouseLeave={() => setHoveredItem(null)}
                        >
                          
                          <Link
                            href={`/research/${item.id}`}
                            className="block w-full text-left p-3 sm:p-4 pr-10 min-h-[56px] relative"
                            onClick={(e) => {
                              // Only prevent default if we're just closing the sidebar
                              if (!isOpen) {
                                e.preventDefault();
                              }
                              // Call onSelectResearch only if we're actually navigating
                              if (isOpen) {
                                onSelectResearch(item.id);
                              }
                              // Always close the sidebar
                              toggleSidebar();
                            }}
                          >
                            <h3 className="font-medium truncate text-gray-200 text-sm sm:text-base transition-colors duration-200 group-hover:text-teal-400">{item.question}</h3>
                            <p className="text-xs text-gray-400 mt-1.5 flex items-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {formatTimestamp(item.timestamp || (item as any).updated_at || (item as any).created_at)}
                            </p>
                          </Link>
                          
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteResearch(item.id);
                            }}
                            className="absolute top-2 right-2 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-white hover:bg-gray-700"
                            aria-label="Delete research"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </motion.li>
                      ))}
                    </ul>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
      
      {/* Custom scrollbar styles */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.3);
          border-radius: 20px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(45, 212, 191, 0.3);
          border-radius: 20px;
          transition: all 0.3s;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(45, 212, 191, 0.6);
        }
      `}</style>
    </>
  );
};

export default ResearchSidebar;