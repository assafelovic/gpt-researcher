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
    <div className="flex justify-center mt-4">
      <a 
        href={getReportLink('pdf')} 
        className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
        target="_blank"
        rel="noopener noreferrer">
        View as PDF
      </a>
      <a 
        href={getReportLink('docx')} 
        className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
        target="_blank"
        rel="noopener noreferrer">
        Download DocX
      </a>
      {chatBoxSettings?.report_type === 'research_report' && (
        <a
          href={getReportLink('json')}
          className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
          target="_blank"
          rel="noopener noreferrer">
          Download Logs
        </a>
      )}
    </div>
  );
};

export default AccessReport;