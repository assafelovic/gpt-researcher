import Image from "next/image";
import React, { useState, useEffect } from 'react';
import { toast } from "react-hot-toast";
import { markdownToHtml } from '../../helpers/markdownHelper';
import '../../styles/markdown.css';
import { useResearchHistoryContext } from '../../hooks/ResearchHistoryContext';
import { ChatMessage } from '../../types/data';

export default function Report({ answer, researchId }: { answer: string, researchId?: string }) {
    const [htmlContent, setHtmlContent] = useState('');
    const { getChatMessages } = useResearchHistoryContext();
    // Memoize this value to prevent re-renders
    const chatMessages = researchId ? getChatMessages(researchId) : [];

    useEffect(() => {
      if (answer) {
        markdownToHtml(answer).then((html) => setHtmlContent(html));
      }
    }, [answer]);
    
    return (
      <div className="container flex h-auto w-full shrink-0 gap-4 bg-black/30 backdrop-blur-md shadow-lg rounded-lg border border-solid border-gray-700/40 p-5">
        <div className="w-full">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-3">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                width={20}
                height={20}
                fill="none" 
                stroke="currentColor" 
                strokeWidth={1.5} 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="text-teal-200"
              >
                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-sm font-medium text-teal-200">Research Report</h3>
            </div>
            {answer && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(answer.trim());
                    toast("Report copied to clipboard", {
                      icon: "✂️",
                    });
                  }}
                  className="hover:opacity-80 transition-opacity duration-200"
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
            )}
          </div>
          
          <div className="flex flex-wrap content-center items-center gap-[15px] pl-5 pr-5">
            <div className="w-full whitespace-pre-wrap text-base font-light leading-[152.5%] text-white log-message">
              {answer ? (
                <div className="markdown-content prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: htmlContent }} />
              ) : (
                <div className="flex w-full flex-col gap-2">
                  <div className="h-6 w-full animate-pulse rounded-md bg-gray-300/20" />
                  <div className="h-6 w-[85%] animate-pulse rounded-md bg-gray-300/20" />
                  <div className="h-6 w-[90%] animate-pulse rounded-md bg-gray-300/20" />
                  <div className="h-6 w-[70%] animate-pulse rounded-md bg-gray-300/20" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
} 