import React from 'react';
import {getHost} from '../../helpers/getHost'

interface AccessReportProps {
  accessData: {
    pdf?: string;
    docx?: string;
    json?: string;
  };
  chatBoxSettings: {
    report_type?: string;
  };
  report: string;
}

const AccessReport: React.FC<AccessReportProps> = ({ accessData, chatBoxSettings, report }) => {
  const host = getHost();

  const getReportLink = (dataType: 'pdf' | 'docx' | 'json'): string => {
    // Early return if path is not available
    if (!accessData?.[dataType]) {
      console.warn(`No ${dataType} path provided`);
      return '#';
    }

    const path = accessData[dataType] as string;
    
    // Clean the path - remove leading/trailing slashes and handle outputs/ prefix
    const cleanPath = path
      .trim()
      .replace(/^\/+|\/+$/g, ''); // Remove leading/trailing slashes
    
    // Only prepend outputs/ if it's not already there
    const finalPath = cleanPath.startsWith('outputs/') 
      ? cleanPath 
      : `outputs/${cleanPath}`;
    
    return `${host}/${finalPath}`;
  };

  // Safety check for accessData
  if (!accessData || typeof accessData !== 'object') {
    return null;
  }

  return (
    <div className="container rounded-lg border border-solid border-gray-700/30 bg-black/30 backdrop-blur-md shadow-lg p-5 my-5">
      <div className="flex flex-col items-center">
        <h3 className="text-lg font-bold mb-4 text-white">Access Your Research Report</h3>
        
        <div className="flex flex-wrap justify-center gap-3">
          <a 
            href={getReportLink('pdf')} 
            className="bg-teal-600 text-white font-medium uppercase text-sm px-6 py-3 rounded-lg shadow-md hover:shadow-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-teal-500/50 transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            target="_blank"
            rel="noopener noreferrer">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            View as PDF
          </a>
          
          <a 
            href={getReportLink('docx')} 
            className="bg-blue-500 text-white font-medium uppercase text-sm px-6 py-3 rounded-lg shadow-md hover:shadow-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-blue-400/50 transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            target="_blank"
            rel="noopener noreferrer">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download DocX
          </a>
          
          {chatBoxSettings?.report_type === 'research_report' && (
            <a
              href={getReportLink('json')}
              className="bg-cyan-600 text-white font-medium uppercase text-sm px-6 py-3 rounded-lg shadow-md hover:shadow-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
              target="_blank"
              rel="noopener noreferrer">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
              Download Logs
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccessReport;