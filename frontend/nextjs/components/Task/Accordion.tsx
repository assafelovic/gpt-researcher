// Accordion.tsx
import { useState } from 'react';

type ProcessedData = {
  field: string;
  isMarkdown: boolean;
  htmlContent: string | object;
};

type Log = {
  header: string;
  text: string;
  processedData?: ProcessedData[];
};

interface AccordionProps {
  logs: Log[];
}

const plainTextFields = ['task', 'sections', 'headers', 'sources', 'research_data'];

const Accordion: React.FC<AccordionProps> = ({ logs }) => {

  const getLogHeaderText = (log: Log): string => {
    const regex = /📃 Source: (https?:\/\/[^\s]+)/;
    const match = log.text.match(regex);
    let sourceUrl = '';

    if (match) {
      sourceUrl = match[1];
    }

    return log.header === 'differences'
      ? 'The following fields on the Langgraph were updated: ' + Object.keys(JSON.parse(log.text).data).join(', ')
      : `📄 Retrieved relevant content from the source: ${sourceUrl}`;
  };

  const renderLogContent = (log: Log) => {
    if (log.header === 'differences' && log.processedData) {
      return log.processedData.map((data, index) => (
        <div key={index} className="mb-4">
          <h3 className="font-semibold text-lg text-body-color dark:text-dark-6">{data.field}:</h3>
          {data.isMarkdown ? (
            <div className="markdown-content" dangerouslySetInnerHTML={{ __html: data.htmlContent as string }} />
          ) : (
            <p className="text-body-color dark:text-dark-6">
              {typeof data.htmlContent === 'object' ? JSON.stringify(data.htmlContent) : data.htmlContent}
            </p>
          )}
          <style jsx>{`
            .markdown-content {
              margin: 0;
              padding: 0;
              h1, h2, h3, h4, h5, h6 {
                font-size: inherit;
                font-weight: bold;
                margin-top: 1em;
                margin-bottom: 0.2em;
                line-height: 1.2;
              }
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
              ul {
                list-style-type: none;
                padding-left: 0;
                margin-top: 1em;
                margin-bottom: 1em;
              }
              ul > li {
                margin-bottom: 0.5em;
              }
              ul > li > ul {
                margin-left: 1em;
                list-style-type: disc;
              }
              ul > li > ul > li {
                margin-bottom: 0.3em;
              }
              ul > li > ul > li > ul {
                margin-left: 1em;
                list-style-type: circle;
              }
              ul > li > ul > li > ul > li {
                margin-bottom: 0.2em;
              }
            }
          `}</style>
        </div>
      ));
    } else {
      return <p className="mb-2 text-body-color dark:text-dark-6">{log.text}</p>;
    }
  };

  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleToggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div id="accordion-collapse" data-accordion="collapse" className="mt-4 bg-gray-900 rounded-lg">
      {logs.map((log, index) => (
        <div key={index}>
          <h2 id={`accordion-collapse-heading-${index}`}>
            <button
              type="button"
              className="flex items-center w-full p-5 font-medium rtl:text-right text-white rounded-t-xl gap-3"
              onClick={() => handleToggle(index)}
              aria-expanded={openIndex === index}
              aria-controls={`accordion-collapse-body-${index}`}
            >
              <span className="flex-grow text-left">{getLogHeaderText(log)}</span>
              <svg
                data-accordion-icon
                className={`w-3 h-3 ${openIndex === index ? 'rotate-180' : ''} shrink-0`}
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 10 6"
              >
                <path
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 5 5 1 1 5"
                />
              </svg>
            </button>
          </h2>
          <div
            id={`accordion-collapse-body-${index}`}
            className={`${openIndex === index ? '' : 'hidden'}`}
            aria-labelledby={`accordion-collapse-heading-${index}`}
          >
            <div className="p-5 border border-b-0 border-gray-900 dark:border-gray-900 dark:bg-gray-900 text-white">
              {renderLogContent(log)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Accordion;