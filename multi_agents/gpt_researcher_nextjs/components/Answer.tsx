import Image from "next/image";
import { Toaster, toast } from "react-hot-toast";

import { useEffect, useState } from 'react';
import { remark } from 'remark';
import html from 'remark-html';


export default function Answer({ answer }: { answer: string }) {
  async function markdownToHtml(markdown) {
    try {
      const result = await remark().use(html).process(markdown);
      console.log('Markdown to HTML conversion result:', result.toString());
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
    <div className="container flex h-auto w-full shrink-0 gap-4 rounded-lg border border-solid border-[#C2C2C2] bg-white p-5 lg:p-10">
      <div className="hidden lg:block">
        <Image src="/img/Info.svg" alt="footer" width={24} height={24} />
      </div>
      <div className="w-full">
        <div className="flex items-center justify-between pb-3">
          <div className="flex gap-4">
            <Image
              src="/img/Info.svg"
              alt="footer"
              width={24}
              height={24}
              className="block lg:hidden"
            />
            <h3 className="text-base font-bold uppercase text-black">
              Answer:{" "}
            </h3>
          </div>
          {answer && (
            <div className="flex items-center gap-3">
              {/* <Image
                src="/img/link.svg"
                alt="footer"
                width={20}
                height={20}
                className="cursor-pointer"
              /> */}
              <button
                onClick={() => {
                  navigator.clipboard.writeText(answer.trim());
                  toast("Answer copied to clipboard", {
                    icon: "✂️",
                  });
                }}
              >
                <Image
                  src="/img/copy.svg"
                  alt="footer"
                  width={20}
                  height={20}
                  className="cursor-pointer"
                />
              </button>
              {/* <Image
                src="/img/share.svg"
                alt="footer"
                width={20}
                height={20}
                className="cursor-pointer"
              /> */}
            </div>
          )}
        </div>
        <div className="flex flex-wrap content-center items-center gap-[15px]">
          <div className="w-full whitespace-pre-wrap text-base font-light leading-[152.5%] text-black">
            {answer ? (
              <div>
                <div className="markdown-content" dangerouslySetInnerHTML={{ __html: htmlContent }} />
                <style jsx>{`
                  .markdown-content {
                    /* Reset margins and paddings */
                    margin: 0;
                    padding: 0;
                    /* Override existing styles for headings */
                    h1, h2, h3, h4, h5, h6 {
                      font-size: inherit;
                      font-weight: bold;
                      margin-top: 1em;
                      margin-bottom: 0.2em;
                      line-height: 1.2;
                    }
                    /* Optionally add more specific styling */
                    h1 {
                      font-size: 2.5em;
                      color: #333;
                    }
                    h2 {
                      font-size: 2em;
                      color: #555;
                    }
                    h3 {
                      font-size: 1.5em;
                      color: #777;
                    }
                    h4 {
                      font-size: 1.2em;
                      color: #999;
                    }
                    /* Add more styles as needed */

                    /* Table of Contents Styling */
                    h2 + ul {
                      list-style-type: none;
                      padding-left: 0;
                      margin-top: 1em;
                      margin-bottom: 1em;
                    }
                    h2 + ul > li {
                      margin-bottom: 0.5em;
                    }
                    h2 + ul > li > ul {
                      margin-left: 1em;
                      list-style-type: disc;
                    }
                    h2 + ul > li > ul > li {
                      margin-bottom: 0.3em;
                    }
                    h2 + ul > li > ul > li > ul {
                      margin-left: 1em;
                      list-style-type: circle;
                    }
                    h2 + ul > li > ul > li > ul > li {
                      margin-bottom: 0.2em;
                    }
                  }
                `}</style>
              </div>
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
