export default function AccessReport({accessData, report}){  
  function copyToClipboard(text) {
    if ('clipboard' in navigator) {
      navigator.clipboard.writeText(report);
    } else {
      document.execCommand('copy', true, report);
    }
  }

    const reportAccessLink = `http://localhost:8000/${accessData.output?.replace('./', '')}`

    return (
      <div>
        <button onClick={copyToClipboard()} className="btn btn-secondary mt-3">Copy to clipboard</button>
        <a id="downloadLink" href={reportAccessLink} className="btn btn-secondary mt-3" target="_blank">View as PDF</a>
      </div>
    );
  }

