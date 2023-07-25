export default function AccessReport(){  
    const copyToClipboard = () => {
        const textarea = document.createElement('textarea');
        textarea.id = 'temp_element';
        textarea.style.height = 0;
        document.body.appendChild(textarea);
        textarea.value = document.getElementById('reportContainer')?.innerText;
        const selector = document.querySelector('#temp_element');
        selector.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }

    return (
      <div>
        <button onClick={copyToClipboard()} className="btn btn-secondary mt-3">Copy to clipboard</button>
        <a id="downloadLink" href="#" className="btn btn-secondary mt-3" target="_blank">Download as PDF</a>
      </div>
    );
  }

