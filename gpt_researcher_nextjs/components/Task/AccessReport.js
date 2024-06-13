export default function AccessReport({ accessData, report }) {
  const getHost = () => {
    if (typeof window !== 'undefined') {
      let { host } = window.location;
      return host.includes('localhost') ? 'localhost:8000' : host;
    }
    return '';
  };

  const host = getHost();

  function copyToClipboard(text) {
    if ('clipboard' in navigator) {
      navigator.clipboard.writeText(report);
    } else {
      document.execCommand('copy', true, report);
    }
  }

  const getReportLink = (dataType) => {
    return `http://${host}/${accessData[dataType]}`;
  };

  return (
    <div>
      <a id="downloadLink" href={getReportLink('pdf')} className="btn btn-secondary mt-3" target="_blank">
        View as PDF
      </a>
      <a id="downloadLink" href={getReportLink('docx')} className="btn btn-secondary mt-3" target="_blank">
        Download docX
      </a>
    </div>
  );
}