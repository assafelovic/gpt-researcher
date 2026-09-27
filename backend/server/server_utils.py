import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from gpt_researcher import GPTResearcher
from gpt_researcher.document.document import DocumentLoader

async def execute_multi_agents(query: str, report_type: str = "research_report"):
    """
    Executes the GPT Researcher agent workflow for a given query and report type.
    """
    try:
        # Initialize the GPT Researcher instance
        researcher = GPTResearcher(query=query, report_type=report_type, config_path=None)
        
        # Conduct research on the topic
        await researcher.conduct_research()
        
        # Generate the final report
        report = await researcher.write_report()
        return {"status": "success", "report": report}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def handle_websocket_communication(websocket: WebSocket):
    """
    Manages real-time communication over WebSockets to stream agent progress,
    logs, and research updates back to the client interface.
    """
    await websocket.accept()
    try:
        while True:
            # Receive incoming JSON payloads from the client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            query = message_data.get("query", "")
            report_type = message_data.get("report_type", "research_report")
            
            if not query:
                await websocket.send_text(json.dumps({"type": "error", "content": "Query cannot be empty."}))
                continue
                
            # Send initial progress status
            await websocket.send_text(json.dumps({"type": "logs", "content": f"Starting research for: '{query}'"}))
            
            # Initialize researcher
            researcher = GPTResearcher(query=query, report_type=report_type)
            
            # Stream progress updates (mocking live feedback steps)
            await websocket.send_text(json.dumps({"type": "logs", "content": "Browsing and gathering relevant sources..."}))
            await researcher.conduct_research()
            
            await websocket.send_text(json.dumps({"type": "logs", "content": "Synthesizing findings into final report..."}))
            report = await researcher.write_report()
            
            # Send final completed report back through the socket
            await websocket.send_text(json.dumps({
                "type": "report",
                "content": report
            }))
            
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
        except:
            pass