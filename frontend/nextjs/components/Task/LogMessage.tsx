// LogMessage.tsx
import Accordion from './Accordion';
import { useEffect, useState } from 'react';
import { remark } from 'remark';
import html from 'remark-html';
import ImagesCarousel from './ImagesCarousel';

type ProcessedData = {
  field: string;
  htmlContent: string;
  isMarkdown: boolean;
};

type Log = {
  header: string;
  text: string;
  processedData?: ProcessedData[];
};

interface LogMessageProps {
  logs: Log[];
}

const LogMessage: React.FC<LogMessageProps> = ({ logs }) => {
  const [processedLogs, setProcessedLogs] = useState<Log[]>([]);

  useEffect(() => {
    const processLogs = async () => {
      const newLogs = await Promise.all(
        logs.map(async (log) => {
          if (log.header === 'differences') {
            const data = JSON.parse(log.text).data;
            const processedData = await Promise.all(
              Object.keys(data).map(async (field) => {
                const fieldValue = data[field].after || data[field].before;
                if (!plainTextFields.includes(field)) {
                  const htmlContent = await markdownToHtml(fieldValue);
                  return { field, htmlContent, isMarkdown: true };
                }
                return { field, htmlContent: fieldValue, isMarkdown: false };
              })
            );
            return { ...log, processedData };
          }
          return log;
        })
      );
      setProcessedLogs(newLogs);
    };

    processLogs();
  }, [logs]);

  return (
    <section className="relative z-20 overflow-hidden pb-12 pt-20 lg:pb-[20px] lg:pt-[20px]">
      <div className="container mx-auto">
        <div className="-mx-4 flex flex-wrap justify-center">
          <div className="w-full px-4">
            {processedLogs.map((log, index) => {
              if (log.header === 'subquery_context_window' || log.header === 'differences') {
                return <Accordion key={index} logs={[log]} />;
              } else if(log.header === 'scraping_images') {
                return (
                  <ImagesCarousel
                    images={log.metadata}
                  />
                )
              } else if(log.header !== "selected_images") {
                return (
                  <div
                    key={index}
                    className="mb-4 w-full max-w-4xl mx-auto rounded-lg p-4 bg-gray-800 shadow-md"
                  >
                    <p className="py-3 text-base leading-relaxed text-white dark:text-white">
                      {log.text}
                    </p>
                  </div>
                );
              }
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

const markdownToHtml = async (markdown: string): Promise<string> => {
  try {
    const result = await remark().use(html).process(markdown);
    return result.toString();
  } catch (error) {
    console.error('Error converting Markdown to HTML:', error);
    return ''; // Handle error gracefully, return empty string or default content
  }
};

const plainTextFields = ['task', 'sections', 'headers', 'sources', 'research_data'];

export default LogMessage;