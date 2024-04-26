export default function AccessReport({accessData, report}){  
  function copyToClipboard(text) {
    if ('clipboard' in navigator) {
      navigator.clipboard.writeText(report);
    } else {
      document.execCommand('copy', true, report);
    }
  }

  const getReportLink = () => {
    const output = accessData.output;

    console.log('output', output);

    if (output && typeof output === 'string') {
      return `http://localhost:8000/${output.replace('./', '')}`;
      // Now you can use reportAccessLink
    } else {
      return `http://localhost:8000/${accessData.output}`
    } 
  }

  return (
    <div>
      {/* <button onClick={copyToClipboard()} className="btn btn-secondary mt-3">Copy to clipboard</button> */}
      <a id="downloadLink" href={getReportLink()} className="btn btn-secondary mt-3" target="_blank">View as PDF</a>
    </div>
  );
}