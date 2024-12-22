import React from 'react';
import {getHost} from '../../helpers/getHost'

interface AccessReportProps {
  accessData: {
    pdf?: string;
    docx?: string;
    json?: string;
  };
  chatBoxSettings: any;
  logs?: any[];
  report: string;
}

const AccessReport: React.FC<AccessReportProps> = ({ accessData, chatBoxSettings, report }) => {
  const host = getHost();

  const getReportLink = (dataType: 'pdf' | 'docx' | 'json'): string => {
    if (!accessData[dataType]) {
      console.warn(`No ${dataType} path provided`);
      return '#';
    }

    // Ensure path starts with outputs/
    let path = accessData[dataType];
    if (!path.startsWith('outputs/')) {
      path = `outputs/${path}`;
    }
    
    return `${host}/${path}`;
  };

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
      <a
        href={getReportLink('json')}
        className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
        target="_blank"
        rel="noopener noreferrer">
        Download Logs
      </a>
    </div>
  );
};

export default AccessReport;