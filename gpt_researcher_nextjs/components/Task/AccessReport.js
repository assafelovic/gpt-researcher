let { host } = window.location;
host = host.includes('localhost') ? 'localhost:8000' : host;

export default function AccessReport({accessData, report}){  
  function copyToClipboard(text) {
    if ('clipboard' in navigator) {
      navigator.clipboard.writeText(report);
    } else {
      document.execCommand('copy', true, report);
    }
  }

  const getReportLink = (dataType) => {
      return `http://localhost:8000/${accessData[dataType]}`
  }

  return (
    <div>
      <a id="downloadLink" href={getReportLink('pdf')} className="btn btn-secondary mt-3" target="_blank">View as PDF</a>
      <a id="downloadLink" href={getReportLink('docx')} className="btn btn-secondary mt-3" target="_blank">Download docX</a>
    </div>
  );
}