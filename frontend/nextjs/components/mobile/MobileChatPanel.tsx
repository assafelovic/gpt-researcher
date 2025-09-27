import React, { useState, useRef, useEffect, useCallback, memo, useMemo } from 'react';
import LoadingDots from '@/components/LoadingDots';
import { Data, ChatData } from '@/types/data';
import { markdownToHtml } from '@/helpers/markdownHelper';
import '@/styles/markdown.css';
import Link from "next/link";
// Simple classname utility function to replace cn from @/lib/utils
const cn = (...classes: (string | undefined)[]) => classes.filter(Boolean).join(' ');
import { toast } from 'react-hot-toast';
import { motion, AnimatePresence } from "framer-motion";
// Remove SendIcon import and use inline SVG instead

interface MobileChatPanelProps {
  question: string;
  chatPromptValue: string;
  setChatPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleChat: (message: string) => void;
  orderedData: Data[];
  loading: boolean;
  isProcessingChat: boolean;
  isStopped: boolean;
  onNewResearch?: () => void;
  className?: string;
}

// Memoize the chat message component to prevent re-rendering all messages
const ChatMessage = memo(({ 
  type, 
  content, 
  html, 
  metadata 
}: { 
  type: string, 
  content: string, 
  html: string, 
  metadata?: any 
}) => {
  if (type === 'question') {
    // User question - now with teal/turquoise color to match theme
    return (
      <div className="flex items-start justify-end space-x-2 py-1 max-w-full animate-fade-in">
        <div className="flex-1 bg-teal-600/80 border border-teal-500/50 rounded-2xl px-4 py-3 text-sm text-white font-medium ml-10 shadow-md">
          {content}
        </div>
        <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center flex-shrink-0 shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="9" r="5" />
            <path d="M3,20 c0,-4 8,-4 8,-4 s8,0 8,4" />
            <path d="M8,10 a4,3 0 0,0 8,0" fill="none" />
          </svg>
        </div>
      </div>
    );
  } else if (type === 'chat') {
    // Check if we have sources from a web search tool call
    const hasWebSources = metadata?.tool_calls?.some(
      (tool: any) => tool.tool === 'quick_search' && tool.search_metadata?.sources?.length > 0
    );
    
    // Get all sources from web searches
    const webSources = metadata?.tool_calls
      ?.filter((tool: any) => tool.tool === 'quick_search')
      .flatMap((tool: any) => tool.search_metadata?.sources || [])
      .map((source: any) => ({
        name: source.title,
        url: source.url
      })) || [];
    
    // Also check for direct sources in metadata (for backward compatibility)
    const directSources = metadata?.sources?.map((source: any) => ({
      name: source.title || source.url,
      url: source.url
    })) || [];
    
    // Combine sources from both locations
    const allSources = [...webSources, ...directSources];
    const hasSources = allSources.length > 0;
    
    // AI response - with darker color
    return (
      <div className="flex flex-col space-y-2 py-1 max-w-full animate-fade-in">
        <div className="flex items-start space-x-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0 shadow-md">
            <img src="/img/gptr-logo.png" alt="AI" className="w-6 h-6" />
          </div>
          <div className="flex-1 ai-message-bubble rounded-2xl px-4 py-3 text-sm text-white mr-4 shadow-lg">
            <div className="markdown-content prose prose-sm prose-invert max-w-none">
              <div dangerouslySetInnerHTML={{ __html: html }} />
            </div>
            
            {/* Collapsed sources UI (old way) - still included for toggle behavior */}
            {metadata && 
             metadata.sources && 
             metadata.sources.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-700/50 text-xs text-gray-200">
                <details className="group">
                  <summary className="cursor-pointer hover:text-white flex items-center">
                    <span className="mr-1">Sources</span>
                    <svg className="h-3 w-3 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <ul className="mt-1 ml-4 space-y-1 list-disc">
                    {metadata.sources.map((source: any, i: number) => (
                      <li key={i}>
                        <a 
                          href={source.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-teal-300 hover:text-teal-200 hover:underline truncate block"
                        >
                          {source.title || source.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </details>
              </div>
            )}
          </div>
        </div>
        
        {/* Source cards display - similar to Sources component with compact=true */}
        {hasSources && (
          <div className="ml-10 mr-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/20 border border-blue-500/30">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="2" y1="12" x2="22" y2="12"></line>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
              </div>
              <span className="text-xs font-medium text-blue-300">Sources</span>
            </div>
            <div className="max-h-[180px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-300/10">
              <div className="flex w-full flex-wrap content-center items-center gap-2">
                {allSources.map((source: {name: string; url: string}, index: number) => {
                  // Extract domain from URL
                  let displayUrl = source.url;
                  try {
                    const urlObj = new URL(source.url);
                    displayUrl = urlObj.hostname.replace(/^www\./, '');
                  } catch (e) {
                    // If URL parsing fails, use the original URL
                  }
                  
                  return (
                    <a 
                      key={`${source.url}-${index}`} 
                      href={source.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-gray-800/60 text-gray-300 hover:text-teal-300 hover:bg-gray-800/90 rounded border border-gray-700/40 transition-colors"
                      title={source.name}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                      </svg>
                      {displayUrl}
                    </a>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
  return null;
});

// Set display name for memo component
ChatMessage.displayName = 'ChatMessage';

// Add markdown processing function if it doesn't exist
function processMarkdown(content: string): string {
  // Simple implementation - in a real app you would use a proper markdown parser
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br />');
}

const MobileChatPanel: React.FC<MobileChatPanelProps> = ({
  question,
  chatPromptValue,
  setChatPromptValue,
  handleChat,
  orderedData,
  loading,
  isProcessingChat,
  isStopped,
  onNewResearch,
  className
}) => {
  const [inputFocused, setInputFocused] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [renderedMessages, setRenderedMessages] = useState<{id: string, content: string, html: string, type: string, metadata?: any}[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const prevOrderedDataLengthRef = useRef(0);
  
  // Process markdown in messages - memoized for performance
  useEffect(() => {
    // Only process if data has changed
    if (orderedData.length === prevOrderedDataLengthRef.current && !loading && !isProcessingChat) {
      return;
    }
    
    // Update reference for comparison
    prevOrderedDataLengthRef.current = orderedData.length;
    
    // Filter to only get chat messages (questions and responses)
    const chatMessages = orderedData.filter((data) => {
      return data.type === 'question' || data.type === 'chat';
    });
    
    const processMessages = async () => {
      try {
        // Process in batches if needed for large message sets
        const rendered = await Promise.all(
          chatMessages.map(async (msg, index) => {
            // For chat messages, convert markdown to HTML
            if (msg.type === 'chat') {
              try {
                const html = await markdownToHtml(msg.content);
                return {
                  id: `${msg.type}-${index}`,
                  content: msg.content,
                  html,
                  type: msg.type,
                  metadata: (msg as ChatData).metadata
                };
              } catch (error) {
                console.error('Error processing markdown:', error);
                // Provide fallback rendering
                return {
                  id: `${msg.type}-${index}`,
                  content: msg.content,
                  html: `<p>${msg.content}</p>`,
                  type: msg.type,
                  metadata: (msg as ChatData).metadata
                };
              }
            } else {
              // For questions, no markdown processing needed
              return {
                id: `${msg.type}-${index}`,
                content: msg.content,
                html: msg.content, // No markdown for questions
                type: msg.type
              };
            }
          })
        );
        
        // Use function form to ensure we're working with latest state
        setRenderedMessages(rendered);
      } catch (error) {
        console.error('Error processing messages:', error);
      }
    };
    
    processMessages();
  }, [orderedData, loading, isProcessingChat]);

  // Auto-resize textarea when content changes - memoized
  const handleTextAreaChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatPromptValue(e.target.value);
    
    if (!inputRef.current) return;
    
    // Reset height to auto to accurately calculate the new height
    inputRef.current.style.height = 'auto';
    
    // Set the height based on the scroll height (content height)
    // with a maximum height
    const newHeight = Math.min(e.target.scrollHeight, 120);
    inputRef.current.style.height = `${newHeight}px`;
  }, [setChatPromptValue]);
  
  // Handle submitting chat messages - memoized
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    if (!chatPromptValue.trim() || isProcessingChat || isSubmitting || isStopped) {
      return;
    }
    
    try {
      setIsSubmitting(true);
      await handleChat(chatPromptValue);
      setChatPromptValue('');
      
      // Focus back on input after sending
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 100);
    } catch (error) {
      console.error('Error submitting chat:', error);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [chatPromptValue, isProcessingChat, isSubmitting, isStopped, setChatPromptValue, handleChat]);
  
  // Handle keyboard shortcuts - memoized
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit();
    }
  }, [handleSubmit]);
  
  // Function to scroll to bottom - memoized
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      const { scrollHeight, clientHeight } = chatContainerRef.current;
      // Only scroll if we're not already at the bottom
      // Add a small buffer to prevent unnecessary scrolls
      const shouldScroll = scrollHeight - chatContainerRef.current.scrollTop - clientHeight > 20;
      
      if (shouldScroll) {
        chatContainerRef.current.scrollTop = scrollHeight;
      }
    }
  }, []);

  // Scroll when messages change or loading/processing state changes
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM has updated
    requestAnimationFrame(() => {
      scrollToBottom();
    });
  }, [renderedMessages.length, loading, isProcessingChat, scrollToBottom]);

  // Also handle mutations in the DOM that might affect scroll height
  useEffect(() => {
    if (!chatContainerRef.current) return;
    
    const observer = new MutationObserver(() => {
      requestAnimationFrame(scrollToBottom);
    });
    
    observer.observe(chatContainerRef.current, {
      childList: true,
      subtree: true,
      characterData: true
    });
    
    return () => observer.disconnect();
  }, [scrollToBottom]);

  // Determine if we need to show intro message
  const showIntroMessage = orderedData.length === 0 || (orderedData.length === 1 && orderedData[0].type === 'question');

  // Optimize the message rendering with better chunking
  const processedMessages = useMemo(() => {
    if (!renderedMessages || renderedMessages.length === 0) return [];
    
    // Process in smaller batches to prevent UI freeze
    // Limit the size of message content to prevent memory issues
    return renderedMessages.map(message => {
      // Trim very long messages to prevent rendering issues
      const processedContent = message.content.length > 50000 
        ? message.content.substring(0, 50000) + "... (message truncated for performance)"
        : message.content;
        
      return {
        ...message,
        content: processedContent,
        processedContent: processMarkdown(processedContent)
      };
    });
  }, [renderedMessages]);

  // Animation variants for preferences modal
  const fadeIn = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.3 } }
  };

  const slideUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } }
  };

  return (
    <div className={cn("flex flex-col h-full bg-gradient-to-b from-gray-900 to-gray-950", className)}>
      {/* Chat Messages Area */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-3 py-2 space-y-3 custom-scrollbar"
      >
        {/* Welcome/Intro message when no content */}
        {showIntroMessage && !loading && (
          <div className="flex items-start space-x-2 py-2 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0 shadow-md">
              <img src="/img/gptr-logo.png" alt="AI" className="w-6 h-6" />
            </div>
            <div className="flex-1 ai-message-bubble rounded-2xl p-4 text-sm text-white shadow-lg">
              <p>Hi there! I&apos;m your research assistant. Type your question and I&apos;ll help you find information and insights.</p>
            </div>
          </div>
        )}
        
        {/* Research in progress message */}
        {loading && renderedMessages.length === 0 && (
          <div className="flex items-start space-x-2 py-2 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0 shadow-md">
              <img src="/img/gptr-logo.png" alt="AI" className="w-6 h-6" />
            </div>
            <div className="flex-1 ai-message-bubble rounded-2xl p-4 text-sm text-white shadow-lg">
              <p>I&apos;m researching your question. This may take a moment...</p>
              <div className="mt-2 flex justify-center">
                <LoadingDots />
              </div>
            </div>
          </div>
        )}
        
        {/* Render chat messages */}
        {processedMessages.map((message) => (
          <ChatMessage 
            key={message.id}
            type={message.type}
            content={message.content}
            html={message.html}
            metadata={message.metadata}
          />
        ))}
        
        {/* Show typing indicator when processing */}
        {isProcessingChat && (
          <div className="flex items-start space-x-2 py-1 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0 shadow-md">
              <img src="/img/gptr-logo.png" alt="AI" className="w-6 h-6" />
            </div>
            <div className="flex-1 ai-message-bubble rounded-2xl px-4 py-3 text-white">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse-slow"></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse-slow animation-delay-200"></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse-slow animation-delay-400"></div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Input Area */}
      <div className={`px-3 py-3 border-t border-gray-800 ${inputFocused ? 'bg-gray-800/90' : 'bg-gray-900/90'} backdrop-blur-sm transition-colors duration-200 safe-bottom`}>
        {!isStopped ? (
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={inputRef}
              value={chatPromptValue}
              onChange={handleTextAreaChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              placeholder="Ask a research question..."
              className="w-full px-4 py-3 pr-14 bg-gray-800/90 border border-gray-700 focus:border-teal-500 rounded-xl resize-none text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-teal-500/50 transition-all shadow-sm"
              style={{ minHeight: '48px', maxHeight: '120px' }}
              disabled={isProcessingChat || isSubmitting}
            />
            
            <button
              type="submit"
              disabled={!chatPromptValue.trim() || isProcessingChat || isSubmitting}
              className={`absolute right-3 bottom-[50%] translate-y-[50%] w-9 h-9 flex items-center justify-center rounded-full ${
                chatPromptValue.trim() && !isProcessingChat && !isSubmitting
                  ? 'bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-white shadow-md'
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              } transition-all duration-200`}
            >
              {isProcessingChat || isSubmitting ? (
                <div className="flex justify-center items-center">
                  <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
                </div>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9"></polygon>
                </svg>
              )}
            </button>
          </form>
        ) : (
          <div className="text-center p-3 text-gray-300 bg-gray-800/60 rounded-xl border border-gray-700/50 text-sm shadow-sm">
            Research has been stopped. 
            {onNewResearch && (
              <button 
                onClick={onNewResearch} 
                className="ml-2 text-teal-400 hover:text-teal-300 hover:underline font-medium"
              >
                Start new research
              </button>
            )}
          </div>
        )}
      </div>

      {/* Custom animations and styles */}
      <style jsx global>{`
        @keyframes fade-in {
          0% {
            opacity: 0;
            transform: translateY(8px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }

        @keyframes pulse-slow {
          0%, 100% {
            opacity: 0.5;
          }
          50% {
            opacity: 1;
          }
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 1.5s infinite;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
        }
        
        .animation-delay-400 {
          animation-delay: 0.4s;
        }
        
        /* Custom scrollbar */
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
        
        /* AI message bubble with subtle gradient */
        .ai-message-bubble {
          background: linear-gradient(145deg, rgba(31, 41, 55, 0.95), rgba(17, 24, 39, 0.9));
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.05);
          position: relative;
          overflow: hidden;
        }
        
        .ai-message-bubble::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 40%;
          background: linear-gradient(to bottom, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0));
          pointer-events: none;
          z-index: 0;
        }
        
        .ai-message-bubble > * {
          position: relative;
          z-index: 1;
        }
        
        /* Improved markdown content styling */
        .markdown-content {
          line-height: 1.6;
        }
        
        .markdown-content ul, .markdown-content ol {
          padding-left: 1.5rem;
        }
        
        .markdown-content code {
          background: rgba(0, 0, 0, 0.2);
          padding: 0.1em 0.3em;
          border-radius: 0.25rem;
          font-size: 0.875em;
        }
        
        .markdown-content pre {
          background: rgba(0, 0, 0, 0.2);
          padding: 0.75rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 0.75rem 0;
        }
        
        .markdown-content pre code {
          background: transparent;
          padding: 0;
        }
        
        .markdown-content a {
          color: #5eead4;
          text-decoration: none;
        }
        
        .markdown-content a:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
};

export default MobileChatPanel; 