import React, { useState } from 'react';
import FileUpload from '../Settings/FileUpload';

export default function ResearchForm({ onFormSubmit, chatBoxSettings }) {
    // Declare a new state variable, which we'll call "count"
    const [count, setCount] = useState(0);
    let {currentReportType, currentReportSource} = chatBoxSettings;


    return (
        <form method="POST" className="mt-3" onSubmit={onFormSubmit}>
            <div className="form-group">
                <label htmlFor="task" className="agent_question">What would you like me to research next?</label>
                <input type="text" name="task" className="form-control" required />
            </div>
            <div className="form-group">
                <label htmlFor="report_type" className="agent_question">What type of report would you like me to
                    generate?</label>
                <select name="report_type" defaultValue={currentReportType} className="form-control" required>
                    <option value="multi_agents">Multi Agents</option>
                    <option value="research_report">Research Report</option>
                    <option value="resource_report">Resource Report</option>
                    <option value="outline_report">Outline Report</option>
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="report_source" className="agent-question">Report Source</label>
                <select name="report_source" defaultValue={currentReportSource} className="form-control" required>
                    <option value="web">The Internet</option>
                    <option value="local">My Documents</option>
                </select>
            </div>
            <FileUpload />
            <input type="submit" value="Research" className="btn btn-primary button-padding" />
        </form>
    );
}