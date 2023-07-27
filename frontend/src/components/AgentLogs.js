export default function AgentLogs(props){  
  const renderAgentLogs = (agentLogs)=>{
    return agentLogs && agentLogs.map((agentLog)=>{
      return (<div class="agent_response">{agentLog.output}</div>)
    })
  }

  return (
    <div className="margin-div">
        <h2>Agent Output</h2>
        <div id="output">
          {JSON.stringify(props)}
        </div>
    </div>
  );
}