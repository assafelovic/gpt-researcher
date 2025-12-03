import React, { useRef, useState, useEffect } from "react";
import { useResearchHistoryContext } from "@/hooks/ResearchHistoryContext";
import MobileChatPanel from "@/components/mobile/MobileChatPanel";
import { ChatBoxSettings, Data, ChatData, QuestionData, ChatMessage } from "@/types/data";
import { toast } from "react-hot-toast";

interface MobileResearchContentProps {
  orderedData: Data[];
  answer: string;
  loading: boolean;
  isStopped: boolean;
  chatPromptValue: string;
  setChatPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleChat: (message: string) => void;
  isProcessingChat?: boolean;
  onNewResearch?: () => void;
  currentResearchId?: string;
  onShareClick?: () => void;
}

export default function MobileResearchContent({
  orderedData: initialOrderedData,
  answer: initialAnswer,
  loading: initialLoading,
  isStopped,
  chatPromptValue,
  setChatPromptValue,
  handleChat: parentHandleChat, // Renamed to clarify it's the parent's handler
  isProcessingChat: parentIsProcessing = false,
  onNewResearch,
  currentResearchId,
  onShareClick
}: MobileResearchContentProps) {
  // Access research history context for saving chat messages
  const { 
    addChatMessage, 
    updateResearch, 
    getChatMessages 
  } = useResearchHistoryContext();
  
  // Create local state to fully control the mobile experience
  const [localOrderedData, setLocalOrderedData] = useState<Data[]>(initialOrderedData);
  const [localAnswer, setLocalAnswer] = useState(initialAnswer);
  const [localLoading, setLocalLoading] = useState(initialLoading);
  const [localProcessing, setLocalProcessing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Sync with parent props when they change
  useEffect(() => {
    setLocalOrderedData(initialOrderedData);
  }, [initialOrderedData]);
  
  useEffect(() => {
    setLocalAnswer(initialAnswer);
  }, [initialAnswer]);
  
  useEffect(() => {
    setLocalLoading(initialLoading);
  }, [initialLoading]);
  
  // Handle chat message submission directly within the component
  const handleLocalChat = async (message: string) => {
    // Prevent processing if already in progress
    if (localProcessing) {
      return;
    }
    
    // Begin processing - show loading indicator
    setLocalProcessing(true);
    
    // Immediately add user question to UI for better UX
    const questionData: QuestionData = { 
      type: 'question', 
      content: message 
    };
    
    setLocalOrderedData(prev => [...prev, questionData]);
    
    // Create a user message object for history saving
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: Date.now()
    };
    
    // If we have a research ID, save the message to history
    if (currentResearchId) {
      try {
        await addChatMessage(currentResearchId, userMessage);
      } catch (error) {
        console.error('Error saving chat message to history:', error);
      }
    }
    
    try {
      // Get chat settings from localStorage or use defaults
      const reportSource = window.localStorage.getItem('chatBoxSettings') ? 
        JSON.parse(window.localStorage.getItem('chatBoxSettings') || '{}').report_source || 'web' :
        'web';
        
      const tone = window.localStorage.getItem('chatBoxSettings') ?
        JSON.parse(window.localStorage.getItem('chatBoxSettings') || '{}').tone || 'Objective' :
        'Objective';
      
      // Get all existing chat messages for context if we have a research ID
      const existingMessages = currentResearchId ? 
        getChatMessages(currentResearchId) : [];
      
      // Format messages to include just role and content
      const formattedMessages = [...existingMessages, userMessage].map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Directly call the chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: formattedMessages,
          report: localAnswer || '',
          report_source: reportSource,
          tone: tone
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.response && data.response.content) {
        // Create the chat response object for history saving
        const aiMessage: ChatMessage = {
          role: 'assistant',
          content: data.response.content,
          timestamp: Date.now(),
          metadata: data.response.metadata
        };
        
        // Create the chat response data for UI
        const chatData: ChatData = { 
          type: 'chat', 
          content: data.response.content,
          metadata: data.response.metadata 
        };
        
        // Update local ordered data with the response
        setLocalOrderedData(prev => [...prev, chatData]);
        
        // If we have a research ID, save the AI message to history
        if (currentResearchId) {
          try {
            // Add AI message to chat history
            await addChatMessage(currentResearchId, aiMessage);
            
            // Update the research with both question and answer
            const updatedOrderedData = [...localOrderedData, questionData, chatData];
            await updateResearch(currentResearchId, localAnswer, updatedOrderedData);
          } catch (error) {
            console.error('Error saving AI response to history:', error);
          }
        }
      } else {
        // Show error for invalid or empty response
        const errorData: ChatData = {
          type: 'chat',
          content: 'Sorry, I couldn\'t generate a proper response. Please try again.'
        };
        
        setLocalOrderedData(prev => [...prev, errorData]);
        toast.error("Received an invalid response from the server", {
          duration: 3000,
          position: "bottom-center"
        });
      }
    } catch (error) {
      // Handle network or processing errors
      console.error('Error in mobile chat:', error);
      
      const errorData: ChatData = {
        type: 'chat',
        content: 'Sorry, there was an error processing your request. Please try again.'
      };
      
      setLocalOrderedData(prev => [...prev, errorData]);
      toast.error("Failed to communicate with the server", {
        duration: 3000,
        position: "bottom-center"
      });
    } finally {
      // Always end processing state
      setLocalProcessing(false);
      
      // Scroll to the bottom to show the new messages
      setTimeout(() => {
        if (bottomRef.current) {
          bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  };
  
  // Extract the initial question from ordered data
  const initialQuestion = localOrderedData.find(data => data.type === 'question');
  const questionText = initialQuestion?.content || '';

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-gradient-to-b from-gray-900 to-gray-950">
      {/* Status Bar - Shows when researching or can show share button */}
      {(localLoading || localProcessing || (currentResearchId && onShareClick)) && (
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800/90 border-b border-gray-700/50 backdrop-blur-sm">
          {/* Left side - status */}
          <div className="flex items-center">
            {(localLoading || localProcessing) && (
              <>
                <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse mr-2"></div>
                <span className="text-xs text-gray-300">
                  {localLoading ? "Researching..." : "Processing..."}
                </span>
              </>
            )}
            {!localLoading && !localProcessing && currentResearchId && (
              <>
                <div className="w-2 h-2 rounded-full bg-teal-500 mr-2"></div>
                <span className="text-xs text-gray-300">Research complete</span>
              </>
            )}
          </div>
          
          {/* Right side - share button */}
          {!localLoading && !localProcessing && currentResearchId && onShareClick && (
            <button 
              onClick={onShareClick}
              className="flex items-center text-xs px-3 py-1.5 rounded-md bg-gradient-to-r from-teal-700/70 to-teal-600/70 text-teal-200 border border-teal-600/40 shadow-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
                <polyline points="16 6 12 2 8 6"></polyline>
                <line x1="12" y1="2" x2="12" y2="15"></line>
              </svg>
              Share
            </button>
          )}
        </div>
      )}
      
      {/* Main Content - MobileChatPanel */}
      <div className="flex-1 overflow-hidden">
        <MobileChatPanel
          question={questionText}
          chatPromptValue={chatPromptValue}
          setChatPromptValue={setChatPromptValue}
          handleChat={handleLocalChat}
          orderedData={localOrderedData}
          loading={localLoading}
          isProcessingChat={localProcessing}
          isStopped={isStopped}
          onNewResearch={onNewResearch}
        />
      </div>
      
      {/* Reference element for scrolling */}
      <div ref={bottomRef} />
      
      {/* Subtle background pattern for premium feel */}
      <div className="absolute inset-0 bg-gradient-radial from-transparent to-transparent pointer-events-none" style={{ 
        backgroundImage: `radial-gradient(circle at 50% 10%, rgba(56, 189, 169, 0.03) 0%, transparent 70%), radial-gradient(circle at 80% 40%, rgba(56, 178, 169, 0.02) 0%, transparent 60%)` 
      }}></div>
      
      {/* Mobile-specific features/styles */}
      <style jsx global>{`
        /* Safe area insets for iPhone */
        @supports (padding: max(0px)) {
          .safe-bottom {
            padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
          }
          .safe-top {
            padding-top: max(3.5rem, env(safe-area-inset-top) + 3.5rem);
          }
        }
        
        /* Remove tap highlight on mobile */
        * {
          -webkit-tap-highlight-color: transparent;
        }
        
        /* Better scrolling experience on mobile */
        .overflow-scroll {
          -webkit-overflow-scrolling: touch;
        }
        
        /* Animation for loading pulse */
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        .animate-pulse {
          animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>
    </div>
  );
} 