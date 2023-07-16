import logo from './logo.svg';
import './App.css';
import ChatBox from './components/ChatBox'

function App() {  

  return (
    <div className="App">
      <header className="App-header">
      <section class="landing">
        <div class="max-w-5xl mx-auto text-center">
            <h1 class="text-4xl font-extrabold mx-auto lg:text-7xl">
                Say Goodbye to
                <span
                    style="background-image:linear-gradient(to right, #9867F0, #ED4E50); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Hours
                    of Research</span>
            </h1>
            <p class="max-w-5xl mx-auto text-gray-600 mt-8" style="font-size:20px">
                Say Hello to GPT Researcher, your AI mate for rapid insights and comprehensive research. GPT Researcher
                takes care of everything from accurate source gathering to organization of research results - all in one
                platform designed to make your research process a breeze.
            </p>
            <a href="#form" class="btn btn-primary">Get Started</a>
        </div>
    </section>

    <main class="container" id="form">
        <form method="POST" class="mt-3" onsubmit="startResearch(); return false;">
            <div class="form-group">
                <label for="task" class="agent_question">What would you like me to research next?</label>
                <input type="text" name="task" class="form-control" required />
            </div>
            <div class="form-group">
                <label for="agent">Select your agent:</label>
                <div class="row">
                    <div class="col agent-item">
                        <label for="defaultAgent"><img src="/static/defaultAgentAvatar.JPG" class="avatar" /></label>
                        <div class="agent-name">
                          <input type="radio" name="agent" id="defaultAgent"
                                value="Default Agent" />
                                  Default Agent</div>
                    </div>
                    <div class="col agent-item">
                        <label for="businessAnalystAgent"><img src="/static/businessAnalystAgentAvatar.png"
                                class="avatar" /></label>
                        <div class="agent-name"><input type="radio" name="agent" id="businessAnalystAgent"
                                value="Business Analyst Agent" />Business Analyst Agent</div>
                    </div>
                    <div class="col agent-item">
                        <label for="financeAgent"><img src="/static/financeAgentAvatar.png" class="avatar" /></label>
                        <div class="agent-name"><input type="radio" name="agent" id="financeAgent" value="Finance Agent"
                                required />Finance Agent</div>
                    </div>
                    <div class="col agent-item">
                        <label for="travelAgent"><img src="/static/travelAgentAvatar.png" class="avatar" /></label>
                        <div class="agent-name"><input type="radio" name="agent" id="travelAgent"
                                value="Travel Agent" />Travel Agent</div>
                    </div>
                    <div class="col agent-item">
                        <label for="academicResearchAgent"><img src="/static/academicResearchAgentAvatar.png"
                                class="avatar" /></label>
                        <div class="agent-name"><input type="radio" name="agent" id="academicResearchAgent"
                                value="Academic Research Agent" />Academic Research Agent</div>
                    </div>
                    <div class="col agent-item">
                        <label for="computerSecurityanalyst"><img src="/static/computerSecurityanalystAvatar.png"
                                class="avatar" /></label>
                        <div class="agent-name"><input type="radio" name="agent" id="computerSecurityanalyst"
                                value="Computer Security Analyst Agent" />Computer Security Analyst Agent</div>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label for="report_type" class="agent_question">What type of report would you like me to
                    generate?</label>
                <select name="report_type" class="form-control" required>
                    <option value="research_report">Research Report</option>
                    <option value="resource_report">Resource Report</option>
                    <option value="outline_report">Outline Report</option>
                </select>
            </div>
            <input type="submit" value="Research" class="btn btn-primary button-padding" />
        </form>

        <div class="margin-div">
            <h2>Agent Output</h2>
            <div id="output"></div>
        </div>
        <div class="margin-div">
            <h2>Research Report</h2>
            <div id="reportContainer"></div>
            <button onclick="copyToClipboard()" class="btn btn-secondary mt-3">Copy to clipboard</button>
            <a id="downloadLink" href="#" class="btn btn-secondary mt-3" target="_blank">Download as PDF</a>
        </div>
    </main>
      </header>
    </div>
  );
}

export default App;
