import logo from './logo.svg';
import './App.css';
import ChatBox from './components/ChatBox'
import ResearchForm from './components/ResearchForm'

function App() {  

  return (
    <div className="App">
      <header className="App-header">
      <section className="landing">
        <div className="max-w-5xl mx-auto text-center">
            <h1 className="text-4xl font-extrabold mx-auto lg:text-7xl">
                Say Goodbye to
                <span className="sayGoodbye">Hours
                    of Research</span>
            </h1>
            <p className="max-w-5xl mx-auto text-gray-600 mt-8" style="font-size:20px">
                Say Hello to GPT Researcher, your AI mate for rapid insights and comprehensive research. GPT Researcher
                takes care of everything from accurate source gathering to organization of research results - all in one
                platform designed to make your research process a breeze.
            </p>
            <a href="#form" className="btn btn-primary">Get Started</a>
        </div>
    </section>

    <main className="container" id="form">
        <form method="POST" className="mt-3" onSubmit={startResearch()}>
            <div className="form-group">
                <label htmlFor="task" className="agent_question">What would you like me to research next?</label>
                <input type="text" name="task" className="form-control" required />
            </div>
            <div className="form-group">
                <label htmlFor="agent">Select your agent:</label>
                <div className="row">
                    <div className="col agent-item">
                        <label htmlFor="defaultAgent"><img src="/static/defaultAgentAvatar.JPG" className="avatar" /></label>
                        <div className="agent-name">
                          <input type="radio" name="agent" id="defaultAgent"
                                value="Default Agent" />
                                  Default Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="businessAnalystAgent"><img src="/static/businessAnalystAgentAvatar.png"
                                className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="businessAnalystAgent"
                                value="Business Analyst Agent" />Business Analyst Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="financeAgent"><img src="/static/financeAgentAvatar.png" className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="financeAgent" value="Finance Agent"
                                required />Finance Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="travelAgent"><img src="/static/travelAgentAvatar.png" className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="travelAgent"
                                value="Travel Agent" />Travel Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="academicResearchAgent"><img src="/static/academicResearchAgentAvatar.png"
                                className="avatar" /></label>
                        <div className="agent-name"><input type="radio" name="agent" id="academicResearchAgent"
                                value="Academic Research Agent" />Academic Research Agent</div>
                    </div>
                    <div className="col agent-item">
                        <label htmlFor="computerSecurityanalyst"><img src="/static/computerSecurityanalystAvatar.png"
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

        <div className="margin-div">
            <h2>Agent Output</h2>
            <div id="output"></div>
        </div>
        <div className="margin-div">
            <h2>Research Report</h2>
            <div id="reportContainer"></div>
            <button onclick="copyToClipboard()" className="btn btn-secondary mt-3">Copy to clipboard</button>
            <a id="downloadLink" href="#" className="btn btn-secondary mt-3" target="_blank">Download as PDF</a>
        </div>
    </main>
      </header>
    </div>
  );
}

export default App;
