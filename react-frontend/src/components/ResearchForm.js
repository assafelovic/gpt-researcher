import React, { useState } from 'react';

export default function ResearchForm({onFormSubmit}) {
    // Declare a new state variable, which we'll call "count"
    const [count, setCount] = useState(0);

    return (
        <form method="POST" className="mt-3" onSubmit={onFormSubmit}>
            <div className="form-group">
                <label htmlFor="task" className="agent_question">What would you like me to research next?</label>
                <input type="text" name="task" className="form-control" required />
            </div>
            <div className="form-group">
                <label htmlFor="report_type" className="agent_question">What type of report would you like me to
                    generate?</label>
                <select name="report_type" className="form-control" required>
                    <option value="research_report">Research Report</option>
                    <option value="resource_report">Resource Report</option>
                    <option value="outline_report">Outline Report</option>
                </select>
            </div>
            <div class="form-group">
                <label for="report_source" class="agent-question">Report Source</label>
                <select name="report_source" class="form-control" required>
                    <option value="web">The Internet</option>
                    <option value="local">My Documents</option>
                </select>
            </div>
            <input type="submit" value="Research" className="btn btn-primary button-padding" />
        </form>
    );
}