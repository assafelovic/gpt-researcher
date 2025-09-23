import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../../types/data';
import ChatInput from './elements/ChatInput';
import { markdownToHtml } from '../../helpers/markdownHelper';
import '../../styles/markdown.css';

interface ChatInterfaceProps {
  researchId: string;
  reportText: string;
  onAddMessage: (message: ChatMessage) => void;
  messages: ChatMessage[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  researchId, 
  reportText, 
  onAddMessage, 
  messages 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [promptValue, setPromptValue] = useState('');
  const [renderedMessages, setRenderedMessages] = useState<{content: string, html: string, role: string}[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Convert markdown in messages to HTML
  useEffect(() => {
    const renderMessages = async () => {
      const rendered = await Promise.all(
        messages.map(async (msg) => {
          const html = await markdownToHtml(msg.content);
          return {
            content: msg.content,
            html,
            role: msg.role
          };
        })
      );
      setRenderedMessages(rendered);
    };
    
    renderMessages();
  }, [messages]);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [renderedMessages]);

  const handleSubmitPrompt = async (prompt: string) => {
    if (!prompt.trim()) return;
    
    // Add user message to the UI
    const userMessage: ChatMessage = {
      role: 'user',
      content: prompt,
      timestamp: Date.now()
    };
    onAddMessage(userMessage);
    
    // Show loading state
    setIsLoading(true);
    
    try {
      // Make API call to chat endpoint
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report: reportText,
          messages: [...messages, userMessage]
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get chat response');
      }
      
      const data = await response.json();
      
      // Add assistant response to the UI
      if (data.response) {
        onAddMessage(data.response);
      }
    } catch (error) {
      console.error('Error during chat:', error);
      // Show error message in chat
      onAddMessage({
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 mb-4 custom-scrollbar">
        {renderedMessages.length === 0 ? (
          <div className="text-center p-8 rounded-lg bg-gradient-to-r from-gray-900/5 to-gray-800/5 border border-gray-300/20 backdrop-blur-sm relative overflow-hidden">
            {/* Ambient decoration */}
            <div className="absolute -inset-1 bg-gradient-to-r from-teal-500/5 via-purple-500/5 to-cyan-500/5 blur-xl opacity-30 animate-pulse"></div>
            
            {/* Icon */}
            <div className="w-16 h-16 mx-auto mb-4 relative">
              <div className="absolute inset-0 bg-gradient-to-br from-teal-400/30 to-cyan-400/30 rounded-full blur-md animate-pulse"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
            </div>
            
            <h3 className="text-lg font-medium text-white mb-2">Ask a question about this research report</h3>
            <p className="text-sm text-gray-400 max-w-md mx-auto">
              The AI has analyzed all the content and is ready to help you explore the findings. 
              Ask anything about the research, request summaries, or dig deeper into specific topics.
            </p>
          </div>
        ) : (
          <>
            {renderedMessages.map((msg, index) => (
              <div 
                key={index} 
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[80%] p-3 rounded-lg shadow-md ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-teal-500/20' 
                      : 'bg-gradient-to-r from-gray-800 to-gray-900 text-white shadow-gray-700/30'
                  } relative overflow-hidden group transition-all duration-300 hover:shadow-lg`}
                >
                  {/* Add subtle animated gradient effect */}
                  <div className={`absolute inset-0 opacity-10 group-hover:opacity-20 transition-opacity duration-300 ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-br from-teal-300/40 via-transparent to-cyan-300/30' 
                      : 'bg-gradient-to-br from-indigo-400/30 via-transparent to-purple-400/20'
                  } animate-pulse pointer-events-none`}></div>
                  
                  <div 
                    className="markdown-content text-sm sm:text-base relative z-10"
                    dangerouslySetInnerHTML={{ __html: msg.html }}
                  />
                </div>
              </div>
            ))}
            
            {/* Skeleton loader for assistant response */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] p-3 rounded-lg shadow-md bg-gradient-to-r from-gray-800 to-gray-900 text-white shadow-gray-700/30 relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/30 via-transparent to-purple-400/20 opacity-20 animate-pulse"></div>
                  <div className="markdown-content text-sm sm:text-base relative z-10">
                    {/* Heading */}
                    <div className="h-7 bg-gray-700/50 rounded-md w-3/5 mb-4 animate-pulse"></div>
                    
                    {/* Paragraph */}
                    <div className="space-y-2 mb-4">
                      <div className="h-4 bg-gray-700/50 rounded-full w-full animate-pulse"></div>
                      <div className="h-4 bg-gray-700/50 rounded-full w-[95%] animate-pulse"></div>
                      <div className="h-4 bg-gray-700/50 rounded-full w-[98%] animate-pulse"></div>
                      <div className="h-4 bg-gray-700/50 rounded-full w-[90%] animate-pulse"></div>
                    </div>
                    
                    {/* List items */}
                    <div className="space-y-2 mb-4">
                      <div className="flex">
                        <div className="h-4 w-4 rounded-full bg-gray-700/50 mt-1 mr-2 animate-pulse"></div>
                        <div className="h-4 bg-gray-700/50 rounded-full w-[70%] animate-pulse"></div>
                      </div>
                      <div className="flex">
                        <div className="h-4 w-4 rounded-full bg-gray-700/50 mt-1 mr-2 animate-pulse"></div>
                        <div className="h-4 bg-gray-700/50 rounded-full w-[80%] animate-pulse"></div>
                      </div>
                      <div className="flex">
                        <div className="h-4 w-4 rounded-full bg-gray-700/50 mt-1 mr-2 animate-pulse"></div>
                        <div className="h-4 bg-gray-700/50 rounded-full w-[75%] animate-pulse"></div>
                      </div>
                    </div>
                    
                    {/* Code block */}
                    <div className="rounded-md bg-gray-800/70 p-3 mb-4">
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-700/60 rounded-full w-[85%] animate-pulse"></div>
                        <div className="h-4 bg-gray-700/60 rounded-full w-[90%] animate-pulse"></div>
                        <div className="h-4 bg-gray-700/60 rounded-full w-[80%] animate-pulse"></div>
                      </div>
                    </div>
                    
                    {/* Final paragraph */}
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-700/50 rounded-full w-[88%] animate-pulse"></div>
                      <div className="h-4 bg-gray-700/50 rounded-full w-[92%] animate-pulse"></div>
                      <div className="h-4 bg-gray-700/50 rounded-full w-[60%] animate-pulse"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 border-t border-gray-700">
        <ChatInput
          promptValue={promptValue}
          setPromptValue={setPromptValue}
          handleSubmit={handleSubmitPrompt}
          disabled={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatInterface; 