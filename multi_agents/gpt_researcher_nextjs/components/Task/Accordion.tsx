import { useState, useEffect } from 'react';
import { remark } from 'remark';
import html from 'remark-html';

const plainTextFields = ['task', 'sections', 'headers', 'sources', 'research_data'];

const Accordion = ({ logs }) => {
  console.log('logs in Accordion', logs);

  const getLogHeaderText = (log) => {
    return log.header === 'differences'
      ? 'The following fields on the Langgraph were updated: ' + Object.keys(JSON.parse(log.text).data).join(', ')
      : log.header;
  };

  const markdownToHtml = async (markdown) => {
    try {
      const result = await remark().use(html).process(markdown);
      return result.toString();
    } catch (error) {
      console.error('Error converting Markdown to HTML:', error);
      return ''; // Handle error gracefully, return empty string or default content
    }
  };

  const renderLogContent = (log) => {
    if (log.header === 'differences') {
      const data = JSON.parse(log.text).data;
      return Object.keys(data).map((field, index) => {
        const fieldValue = data[field].after || data[field].before;
        const [htmlContent, setHtmlContent] = useState('');
        const [isMarkdown, setIsMarkdown] = useState(false);

        useEffect(() => {
          const checkIfMarkdown = async () => {
            if (plainTextFields.includes(field)) {
              setIsMarkdown(false);
              setHtmlContent(fieldValue);
            } else {
              const html = await markdownToHtml(fieldValue);
              if (html !== fieldValue) {
                setIsMarkdown(true);
                setHtmlContent(html);
              } else {
                setIsMarkdown(false);
                setHtmlContent(fieldValue);
              }
            }
          };
          checkIfMarkdown();
        }, [fieldValue]);

        return (
          <div key={index} className="mb-4">
            <h3 className="font-semibold text-lg text-gray-700 dark:text-gray-300">{field}:</h3>
            {isMarkdown ? (
              <div className="markdown-content" dangerouslySetInnerHTML={{ __html: htmlContent }} />
            ) : (
              <p className="text-gray-600 dark:text-gray-400">{typeof htmlContent === 'object' ? JSON.stringify(htmlContent) : htmlContent}</p>
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
        );
      });
    } else {
      return <p className="mb-2 text-body-color dark:text-dark-6 dark:text-gray-400">{log.text}</p>;
    }
  };

  const [openIndex, setOpenIndex] = useState(null);

  const handleToggle = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div id="accordion-collapse" data-accordion="collapse" className="mb-8 bg-white rounded-t-lg">
      {logs.map((log, index) => (
        <div key={index}>
          <h2 id={`accordion-collapse-heading-${index}`}>
            <button
              type="button"
              className="flex items-center justify-between w-full p-5 font-medium rtl:text-right text-body-color dark:text-dark-6 border border-b-0 border-gray-200 rounded-t-xl focus:ring-4 focus:ring-gray-200 dark:focus:ring-gray-800 dark:border-gray-700 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 gap-3"
              onClick={() => handleToggle(index)}
              aria-expanded={openIndex === index}
              aria-controls={`accordion-collapse-body-${index}`}
            >
              <span>{getLogHeaderText(log)}</span>
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
            <div className="p-5 border border-b-0 border-gray-200 dark:border-gray-700 dark:bg-gray-900">
              {renderLogContent(log)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Accordion;