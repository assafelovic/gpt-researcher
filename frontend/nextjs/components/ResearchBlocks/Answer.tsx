import Image from "next/image";
import { Toaster, toast } from "react-hot-toast";
import { useEffect, useState } from 'react';
import { remark } from 'remark';
import html from 'remark-html';
import { Compatible } from "vfile";
import '@/styles/markdown.css';

export default function Answer({ answer }: { answer: string }) {
  async function markdownToHtml(markdown: Compatible | undefined) {
    try {
      const result = await remark().use(html).process(markdown);
      return result.toString();
    } catch (error) {
      console.error('Error converting Markdown to HTML:', error);
      return ''; // Handle error gracefully, return empty string or default content
    }
  }

    const [htmlContent, setHtmlContent] = useState('');

    useEffect(() => {
      markdownToHtml(answer).then((html) => setHtmlContent(html));
    }, [answer]);
    
    return (
      <div className="container flex h-auto w-full shrink-0 gap-4 bg-gray-900 shadow-md rounded-lg border border-solid border-[#C2C2C2] p-5">
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
                >
                  <Image
                    src="/img/copy-white.svg"
                    alt="footer"
                    width={20}
                    height={20}
                    className="cursor-pointer text-white"
                  />
                </button>
              </div>
            )}
          </div>
          <div className="flex flex-wrap content-center items-center gap-[15px] pl-10 pr-10">
            <div className="w-full whitespace-pre-wrap text-base font-light leading-[152.5%] text-white log-message">
              {answer ? (
                <div className="markdown-content" dangerouslySetInnerHTML={{ __html: htmlContent }} />
              ) : (
                <div className="flex w-full flex-col gap-2">
                  <div className="h-6 w-full animate-pulse rounded-md bg-gray-300" />
                  <div className="h-6 w-full animate-pulse rounded-md bg-gray-300" />
                  <div className="h-6 w-full animate-pulse rounded-md bg-gray-300" />
                  <div className="h-6 w-full animate-pulse rounded-md bg-gray-300" />
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
