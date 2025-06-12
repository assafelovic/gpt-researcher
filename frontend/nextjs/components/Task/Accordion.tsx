// Accordion.tsx
import { useState, useEffect } from 'react';
import { addTargetBlankToLinks } from '../../helpers/markdownHelper';
import '../../styles/markdown.css'; // Import global markdown styles

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
  // State to store processed HTML content
  const [processedLogs, setProcessedLogs] = useState<Log[]>(logs);

  useEffect(() => {
    // Process any markdown HTML content to add target="_blank" to links
    if (logs && logs.length > 0) {
      const newLogs = logs.map(log => {
        if (log.processedData) {
          const newProcessedData = log.processedData.map(data => {
            if (data.isMarkdown && typeof data.htmlContent === 'string') {
              return {
                ...data,
                htmlContent: addTargetBlankToLinks(data.htmlContent)
              };
            }
            return data;
          });
          return { ...log, processedData: newProcessedData };
        }
        return log;
      });
      setProcessedLogs(newLogs);
    }
  }, [logs]);

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
      {processedLogs.map((log, index) => (
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