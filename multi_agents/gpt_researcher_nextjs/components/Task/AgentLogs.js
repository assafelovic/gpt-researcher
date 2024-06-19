export default function AgentLogs({agentLogs}){  
  const renderAgentLogs = (agentLogs)=>{
    return agentLogs && agentLogs.map((agentLog, index)=>{
      return (<div key={index} className="agent_response">{agentLog.output}</div>)
    })
  }

  return (
    <div className="margin-div">
        <h2>Agent Output</h2>
        <div id="output">
          {renderAgentLogs(agentLogs)}
        </div>
    </div>
  );
}