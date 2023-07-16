import React from 'react';
import MarkdownView from 'react-showdown';

export default function Report({data}) {
    const copyToClipboard = () => {
        const textarea = document.createElement('textarea');
        textarea.id = 'temp_element';
        textarea.style.height = 0;
        document.body.appendChild(textarea);
        textarea.value = document.getElementById('reportContainer').innerText;
        const selector = document.querySelector('#temp_element');
        selector.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }

    const markdown = `
        # Welcome to React Showdown :+1:

        To get started, edit the markdown in \`example/src/App.tsx\`.

        | Column 1 | Column 2 |
        |----------|----------|
        | A1       | B1       |
        | A2       | B2       |
    `;

    return (
        <div className="margin-div">
            <h2>Research Report</h2>
            <div id="reportContainer">
                <MarkdownView
                    markdown={markdown}
                    options={{ tables: true, emoji: true }}
                />
            </div>
            <button onClick={copyToClipboard()} className="btn btn-secondary mt-3">Copy to clipboard</button>
            <a id="downloadLink" href="#" className="btn btn-secondary mt-3" target="_blank">Download as PDF</a>
        </div>
    );
};