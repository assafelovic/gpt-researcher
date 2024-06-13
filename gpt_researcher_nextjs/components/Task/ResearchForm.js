import React, { useState } from 'react';
import FileUpload from '../Settings/FileUpload';

export default function ResearchForm({ chatBoxSettings, setChatBoxSettings }) {
    let {currentReportType, currentReportSource} = chatBoxSettings;

    const onFormChange = (e) => {
        const { name, value } = e.target;
        setChatBoxSettings((prevSettings) => ({
            ...prevSettings,
            [name]: value,
        }));
    };

    return (
        <form method="POST" className="mt-3">
            <div className="form-group">
                <label htmlFor="report_type" className="agent_question">What type of report would you like me to
                    generate?</label>
                <select name="report_type" value={currentReportType} onChange={onFormChange} className="form-control" required>
                    <option value="multi_agents">Multi Agents</option>
                    <option value="research_report">Research Report</option>
                    <option value="resource_report">Resource Report</option>
                    <option value="outline_report">Outline Report</option>
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="report_source" className="agent-question">Report Source</label>
                <select name="report_source" value={currentReportSource} onChange={onFormChange} className="form-control" required>
                    <option value="web">The Internet</option>
                    <option value="local">My Documents</option>
                </select>
            </div>
            <FileUpload />
        </form>
    );
}