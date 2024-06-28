import { useState } from 'react';

const Accordion = ({ logs }) => {
  console.log('logs in Accordion', logs);

  const getLogHeaderText = (log) => {
    return log.header === 'differences'
      ? 'The following fields on the Langgraph were updated: ' + Object.keys(JSON.parse(log.text).data).join(', ')
      : log.header;
  };

  const renderLogContent = (log) => {
    if (log.header === 'differences') {
      const data = JSON.parse(log.text).data;
      return Object.keys(data).map((field, index) => {
        const fieldValue = data[field].after || data[field].before;
        return (
          <div key={index} className="mb-4">
            <h3 className="font-semibold text-lg text-gray-700 dark:text-gray-300">{field}:</h3>
            <p className="text-gray-600 dark:text-gray-400">{JSON.stringify(fieldValue, null, 2)}</p>
          </div>
        );
      });
    } else {
      return <p className="mb-2 text-gray-500 dark:text-gray-400">{log.text}</p>;
    }
  };

  const [openIndex, setOpenIndex] = useState(null);

  const handleToggle = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div id="accordion-collapse" data-accordion="collapse" className="pb-8">
      {logs.map((log, index) => (
        <div key={index}>
          <h2 id={`accordion-collapse-heading-${index}`}>
            <button
              type="button"
              className="flex items-center justify-between w-full p-5 font-medium rtl:text-right text-gray-500 border border-b-0 border-gray-200 rounded-t-xl focus:ring-4 focus:ring-gray-200 dark:focus:ring-gray-800 dark:border-gray-700 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 gap-3"
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