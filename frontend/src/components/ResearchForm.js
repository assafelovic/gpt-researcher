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
                <label htmlFor="agent">Select your agent:</label>
                <div className="row">
                    <div className="col agent-item">
                        <label htmlFor="defaultAgent"><img src="defaultAgentAvatar.JPG" className="avatar" /></label>
                        <div className="agent-name">
                        <input type="radio" name="agent" id="defaultAgent"
                                value="Default Agent" />
                                Default Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="businessAnalystAgent"><img src="businessAnalystAgentAvatar.png"
                                className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="businessAnalystAgent"
                                value="Business Analyst Agent" />Business Analyst Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="financeAgent"><img src="financeAgentAvatar.png" className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="financeAgent" value="Finance Agent"
                                required />Finance Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="travelAgent"><img src="travelAgentAvatar.png" className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="travelAgent"
                                value="Travel Agent" />Travel Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="academicResearchAgent"><img src="academicResearchAgentAvatar.png"
                                className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="academicResearchAgent"
                                value="Academic Research Agent" />Academic Research Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="computerSecurityanalyst"><img src="computerSecurityanalystAvatar.png"
                                className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="computerSecurityanalyst"
                                value="Computer Security Analyst Agent" />Computer Security Analyst Agent</div>
                    </div>
                </div>
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
            <input type="submit" value="Research" className="btn btn-primary button-padding" />
        </form>
    );
}