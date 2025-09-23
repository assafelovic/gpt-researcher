import { useRef, Dispatch, SetStateAction, useState, useCallback, useEffect } from "react";
import ResearchPanel from "@/components/research/ResearchPanel";
import CopilotPanel from "@/components/research/CopilotPanel";
import { ChatBoxSettings, Data } from "@/types/data";

interface CopilotResearchContentProps {
  orderedData: Data[];
  answer: string;
  allLogs: any[];
  chatBoxSettings: ChatBoxSettings;
  loading: boolean;
  isStopped: boolean;
  promptValue: string;
  chatPromptValue: string;
  setPromptValue: Dispatch<SetStateAction<string>>;
  setChatPromptValue: Dispatch<SetStateAction<string>>;
  handleDisplayResult: (question: string) => void;
  handleChat: (message: string) => void;
  handleClickSuggestion: (value: string) => void;
  currentResearchId?: string;
  onShareClick?: () => void;
  reset?: () => void;
  isProcessingChat?: boolean;
  onNewResearch?: () => void;
  toggleSidebar?: () => void;
}

export default function CopilotResearchContent({
  orderedData,
  answer,
  allLogs,
  chatBoxSettings,
  loading,
  isStopped,
  promptValue,
  chatPromptValue,
  setPromptValue,
  setChatPromptValue,
  handleDisplayResult,
  handleChat,
  handleClickSuggestion,
  currentResearchId,
  onShareClick,
  reset,
  isProcessingChat = false,
  onNewResearch,
  toggleSidebar
}: CopilotResearchContentProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  // Initialize copilot as hidden when loading
  const [isCopilotVisible, setIsCopilotVisible] = useState(false);
  const [showAnimation, setShowAnimation] = useState(false);
  // Track if user manually closed the copilot panel
  const [userClosedCopilot, setUserClosedCopilot] = useState(false);
  // State for split pane resizing
  const [resizingActive, setResizingActive] = useState(false);
  const [researchPanelWidth, setResearchPanelWidth] = useState(58); // percentage
  const [isMobile, setIsMobile] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const widthRef = useRef(researchPanelWidth);
  const researchPanelRef = useRef<HTMLDivElement>(null);
  const chatPanelRef = useRef<HTMLDivElement>(null);
  const lastUpdateTimeRef = useRef(0);
  
  // Check if we're on mobile
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    
    // Initial check
    checkIfMobile();
    
    // Add event listener for window resize
    window.addEventListener('resize', checkIfMobile);
    
    // Cleanup
    return () => window.removeEventListener('resize', checkIfMobile);
  }, []);
  
  // Create a memoized toggle function that's compatible with Dispatch<SetStateAction<boolean>>
  const toggleCopilotVisibility: Dispatch<SetStateAction<boolean>> = useCallback((value) => {
    // Handle both function and direct value cases
    const newValue = typeof value === 'function' ? value(isCopilotVisible) : value;
    
    // Set state without triggering scroll
    setIsCopilotVisible(newValue);
    
    // Track user's explicit action of closing the panel
    if (newValue === false) {
      setUserClosedCopilot(true);
    }
    
    // If we're showing the copilot, trigger the animation
    if (newValue && !isCopilotVisible) {
      setShowAnimation(true);
    }
    
    // Prevent scroll jumping by keeping current scroll position
    const currentScrollY = window.scrollY;
    
    // Use requestAnimationFrame to restore scroll position after the state update
    requestAnimationFrame(() => {
      window.scrollTo({
        top: currentScrollY,
        behavior: 'auto'
      });
    });
  }, [isCopilotVisible]);
  
  // Effect to handle initial state and research completion
  useEffect(() => {
    // Reset userClosedCopilot when new research starts
    if (loading) {
      setUserClosedCopilot(false);
    }
    
    // Automatically open the copilot when research completes BUT only if user hasn't manually closed it
    if (!loading && answer && !isCopilotVisible && !userClosedCopilot) {
      // Add a slight delay before showing the copilot for a better UX
      const timer = setTimeout(() => {
        setIsCopilotVisible(true);
        setShowAnimation(true);
      }, 800);
      
      return () => clearTimeout(timer);
    }
  }, [loading, answer, isCopilotVisible, userClosedCopilot]);
  
  // Extract the initial question from orderedData
  const initialQuestion = orderedData.find(data => data.type === 'question');
  const questionText = initialQuestion?.content || '';

  // Handle resize start
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setResizingActive(true);
  }, []);

  // Handle resize move
  useEffect(() => {
    const handleResizeMove = (e: MouseEvent) => {
      if (!resizingActive || !containerRef.current) return;
      
      // Throttle updates to every 16ms (approx 60fps)
      const now = Date.now();
      if (now - lastUpdateTimeRef.current < 16) {
        return;
      }
      lastUpdateTimeRef.current = now;
      
      // Use requestAnimationFrame for smoother updates
      requestAnimationFrame(() => {
        if (!containerRef.current) return;
        
        const containerRect = containerRef.current.getBoundingClientRect();
        const containerWidth = containerRect.width;
        const mouseX = e.clientX - containerRect.left;
        
        // Calculate percentage width (with constraints)
        let newWidth = (mouseX / containerWidth) * 100;
        newWidth = Math.max(30, Math.min(70, newWidth)); // Constrain between 30% and 70%
        
        // Store width in ref without causing re-renders
        widthRef.current = newWidth;
        
        // Apply directly to DOM elements using refs
        if (researchPanelRef.current) {
          researchPanelRef.current.style.width = `${newWidth}%`;
        }
        if (chatPanelRef.current) {
          chatPanelRef.current.style.width = `${100 - newWidth}%`;
        }
      });
    };

    const handleResizeEnd = () => {
      // Only update state once dragging ends
      setResearchPanelWidth(widthRef.current);
      setResizingActive(false);
    };

    if (resizingActive) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
    }

    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
    };
  }, [resizingActive]);

  return (
    <div 
      ref={containerRef}
      className="flex flex-col lg:flex-row w-full h-screen gap-1 px-2 lg:px-2 relative"
    >
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900/5 via-gray-800/5 to-gray-900/5 pointer-events-none"></div>
      
      {/* Research Results Panel (Left) */}
      <div 
        ref={researchPanelRef}
        data-panel="research"
        className={`w-full ${isCopilotVisible ? '' : 'lg:w-full'} h-full overflow-hidden flex flex-col bg-gray-900/30 backdrop-blur-sm rounded-lg border border-gray-800/50 shadow-lg ${!resizingActive ? 'transition-width duration-300' : ''}`}
        style={isCopilotVisible && !isMobile ? { width: `${researchPanelWidth}%` } : {}}
      >
        <ResearchPanel 
          orderedData={orderedData}
          answer={answer}
          allLogs={allLogs}
          chatBoxSettings={chatBoxSettings}
          handleClickSuggestion={handleClickSuggestion}
          currentResearchId={currentResearchId}
          onShareClick={onShareClick}
          isCopilotVisible={isCopilotVisible}
          setIsCopilotVisible={toggleCopilotVisibility}
          onNewResearch={onNewResearch}
          loading={loading}
          toggleSidebar={toggleSidebar}
        />
      </div>

      {/* Resizer handle */}
      {isCopilotVisible && (
        <div
          className={`hidden lg:flex flex-col items-center justify-center w-1 h-full cursor-col-resize ${resizingActive ? 'bg-teal-500/50' : 'bg-gray-700/30 hover:bg-teal-500/30'} transition-colors duration-150 active:bg-teal-500/50 z-10 mx-0.5`}
          onMouseDown={handleResizeStart}
        >
          <div className="flex flex-col items-center justify-center">
            <div className="w-0.5 h-16 bg-gray-500/80 rounded-full hover:bg-teal-400/80"></div>
          </div>
        </div>
      )}
      
      {/* Copilot Chat Panel (Right) */}
      {isCopilotVisible && (
        <div 
          ref={chatPanelRef}
          data-panel="chat"
          className={`w-full h-1/2 lg:h-full overflow-hidden flex flex-col bg-gray-900/30 backdrop-blur-sm rounded-lg border border-gray-800/50 shadow-lg ${!resizingActive ? 'transition-width duration-300' : ''} ${
            showAnimation ? 'animate-copilot-entrance' : ''
          }`}
          style={!isMobile ? { width: `${100 - researchPanelWidth}%` } : {}}
        >
          <CopilotPanel
            question={questionText}
            chatPromptValue={chatPromptValue}
            setChatPromptValue={setChatPromptValue}
            handleChat={handleChat}
            orderedData={orderedData}
            loading={loading}
            isProcessingChat={isProcessingChat}
            isStopped={isStopped}
            bottomRef={bottomRef}
            isCopilotVisible={isCopilotVisible}
            setIsCopilotVisible={toggleCopilotVisibility}
          />
        </div>
      )}
      
      {/* Custom styles for animations */}
      <style jsx global>{`
        @keyframes subtle-pulse {
          0% { opacity: 0.8; }
          50% { opacity: 1; }
          100% { opacity: 0.8; }
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        @keyframes spin-slow {
          to { transform: rotate(-360deg); }
        }
        
        @keyframes spin-slower {
          to { transform: rotate(360deg); }
        }
        
        .animate-spin {
          animation: spin 1.5s linear infinite;
        }
        
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
        
        .animate-spin-slower {
          animation: spin-slower 4.5s linear infinite;
        }
        
        @keyframes copilot-entrance {
          0% { 
            opacity: 0; 
            transform: translateX(40px) scale(0.95);
            box-shadow: 0 0 0 rgba(17, 24, 39, 0);
          }
          70% {
            opacity: 1;
            transform: translateX(-5px) scale(1.02);
            box-shadow: 0 10px 25px rgba(17, 24, 39, 0.2);
          }
          100% { 
            opacity: 1; 
            transform: translateX(0) scale(1);
            box-shadow: 0 4px 12px rgba(17, 24, 39, 0.15);
          }
        }
        
        .animate-copilot-entrance {
          animation: copilot-entrance 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        
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

        .transition-width {
          transition: width 0.3s ease;
        }
      `}</style>
    </div>
  );
} 