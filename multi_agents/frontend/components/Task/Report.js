import React from 'react';

export default function Report({report}) {

    return (
        <div>
            <h2>Research Report</h2>
            <div id="reportContainer">
                {/* <MarkdownView
                    markdown={report}
                    options={{ tables: true, emoji: true }}
                /> */}
            </div>
        </div>
    );
};