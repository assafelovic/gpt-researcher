import React, { useState } from 'react';
import FileUpload from '../Settings/FileUpload';

export default function ResearchForm({ chatBoxSettings, setChatBoxSettings }) {
    console.log('chatBoxSettings',chatBoxSettings)

    let {report_type, report_source} = chatBoxSettings;

    const onFormChange = (e) => {
        const { name, value } = e.target;
        setChatBoxSettings((prevSettings) => ({
            ...prevSettings,
            [name]: value,
        }));
    };

    return (
        <form method="POST" className="mt-3" className="report_settings">
            <div className="form-group">
                <label htmlFor="report_type" className="agent_question">Report Type </label>
                <select name="report_type" value={report_type} onChange={onFormChange} className="form-control" required>
                    <option value="multi_agents">Multi Agents</option>
                    <option value="research_report">Research Report</option>
                    <option value="resource_report">Resource Report</option>
                    <option value="outline_report">Outline Report</option>
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="report_source" className="agent_question">Report Source </label>
                <select name="report_source" value={report_source} onChange={onFormChange} className="form-control" required>
                    <option value="web">The Internet</option>
                    <option value="local">My Documents</option>
                </select>
            </div>
            {report_source == 'local' && report_type != 'multi_agents' ? <FileUpload /> : <></>}
        </form>
    );
}