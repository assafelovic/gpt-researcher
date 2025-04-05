import Image from "next/image";
import React from 'react';
import { Toaster, toast } from "react-hot-toast";
import { useEffect, useState } from 'react';
import { markdownToHtml } from '../../helpers/markdownHelper';
import '../../styles/markdown.css';

export default function Answer({ answer }: { answer: string }) {
    const [htmlContent, setHtmlContent] = useState('');

    useEffect(() => {
      if (answer) {
        markdownToHtml(answer).then((html) => setHtmlContent(html));
      }
    }, [answer]);
    
    return (
      <div className="container flex h-auto w-full shrink-0 gap-4 bg-black/30 backdrop-blur-md shadow-lg rounded-lg border border-solid border-gray-700/40 p-5">
        <div className="w-full">
          <div className="flex items-center justify-between pb-3">
            {answer && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(answer.trim());
                    toast("Answer copied to clipboard", {
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
                <div className="markdown-content" dangerouslySetInnerHTML={{ __html: htmlContent }} />
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
        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{ duration: 2000 }}
        />
      </div>
    );
}
