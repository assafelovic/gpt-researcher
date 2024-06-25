// multi_agents/gpt_researcher_nextjs/components/Task/LogMessage.tsx

import Accordion from './Accordion';

const LogMessage = ({ logs }) => {
  return (
    <section className="relative z-20 overflow-hidden bg-white pb-12 pt-20 dark:bg-dark lg:pb-[90px] lg:pt-[120px]">
      <div className="container mx-auto">
        <div className="-mx-4 flex flex-wrap justify-center">
          <div className="w-full px-4 lg:w-3/4">
            {logs.map((log, index) => {
              if (log.header === 'subquery_context_window') {
                return <Accordion key={index} logs={[log]} />;
              } else {
                return (
                  <div key={index} className="mb-8 w-full rounded-lg bg-white p-4 shadow-[0px_20px_95px_0px_rgba(201,203,204,0.30)] dark:bg-dark-2 dark:shadow-[0px_20px_95px_0px_rgba(0,0,0,0.30)] sm:p-8 lg:px-6 xl:px-8">
                    
                    <p className="py-3 text-base leading-relaxed text-body-color dark:text-dark-6">
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

export default LogMessage;