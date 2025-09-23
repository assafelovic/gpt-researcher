import React, { useState, useEffect } from 'react';
import { toast } from "react-hot-toast";
import { markdownToHtml } from '../../helpers/markdownHelper';
import '../../styles/markdown.css';
import Sources from './Sources';

interface ChatResponseProps {
  answer: string;
  metadata?: {
    tool_calls?: Array<{
      tool: string;
      query: string;
      search_metadata: {
        query: string;
        sources: Array<{
          title: string;
          url: string;
          content: string;
        }>
      }
    }>
  }
}

export default function ChatResponse({ answer, metadata }: ChatResponseProps) {
    const [htmlContent, setHtmlContent] = useState('');
    
    // Check if we have sources from a web search tool call
    const hasWebSources = metadata?.tool_calls?.some(
      tool => tool.tool === 'quick_search' && tool.search_metadata?.sources?.length > 0
    );
    
    // Get all sources from web searches
    const webSources = metadata?.tool_calls
      ?.filter(tool => tool.tool === 'quick_search')
      .flatMap(tool => tool.search_metadata?.sources || [])
      .map(source => ({
        name: source.title,
        url: source.url
      })) || [];

    useEffect(() => {
      if (answer) {
        markdownToHtml(answer).then((html) => setHtmlContent(html));
      }
    }, [answer]);
    
    // Format the answer for display
    const formattedAnswer = answer.trim() || 'No answer available.';
    
    const copyToClipboard = () => {
        // Copy the plain text of the answer instead of the HTML
        navigator.clipboard.writeText(formattedAnswer)
            .then(() => {
                toast.success('Copied to clipboard!');
            })
            .catch((err) => {
                console.error('Failed to copy: ', err);
                toast.error('Failed to copy to clipboard');
            });
    };
  
    return (
      <div className="container flex h-auto w-full shrink-0 gap-4 bg-black/30 backdrop-blur-md shadow-lg rounded-lg border border-solid border-gray-700/40 p-5">
        <div className="w-full">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-6 h-6 rounded-md bg-teal-500/20 border border-teal-500/30">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-teal-400">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <h3 className="text-sm font-medium text-teal-200">Answer</h3>
            </div>
            <button 
              onClick={copyToClipboard}
              className="hover:opacity-80 transition-opacity duration-200"
              aria-label="Copy to clipboard"
              title="Copy to clipboard"
            >
              <img
                src="/img/copy-white.svg"
                alt="copy"
                width={20}
                height={20}
                className="cursor-pointer text-white"
              />
            </button>
          </div>
          
          <div className="flex flex-wrap content-center items-center gap-[15px] pl-5 pr-5">
            <div className="w-full whitespace-pre-wrap text-base font-light leading-[152.5%] text-white log-message">
              <div 
                className="markdown-content prose prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: htmlContent }}
              />
            </div>
          </div>
          
          {/* Display web search sources if available */}
          {hasWebSources && webSources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-700/30">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/20 border border-blue-500/30">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                </div>
                <span className="text-xs font-medium text-blue-300">New Sources</span>
              </div>
              <Sources sources={webSources} compact={true} />
            </div>
          )}
        </div>
      </div>
    );
} 