import asyncio
import json
import uuid
from typing import Dict, Optional
from datetime import datetime
import logging
import time

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import your existing modules
from backend.report_type import BasicReport, DetailedReport
from backend.chat import ChatAgentWithMemory
from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task
import redis
import os
from redish_database.redis_context import (chat_exists, create_chat, get_chat_messages,
                                    add_chat_messages, delete_chat, save_full_chat_history_to_redis)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD", None),  # Optional for local setup
    decode_responses=True
)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchRequest(BaseModel):
    task: str
    report_type: str = "research_report"
    report_source: str = "web"
    tone: str = "formal"
    source_urls: list = []
    document_urls: list = []
    headers: dict = None
    query_domains: list = []
    mcp_enabled: bool = False
    mcp_strategy: str = "fast"
    mcp_configs: list = []

class ChatRequest(BaseModel):
    message: str

class SSEResearchManager:
    """Manages research tasks with Server-Sent Events streaming"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict] = {}
        self.task_queues: Dict[str, asyncio.Queue] = {}
        self.chat_agents: Dict[str, ChatAgentWithMemory] = {}
        self.task_results: Dict[str, str] = {}  # Store completed reports
    
    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        return str(uuid.uuid4())
    
    async def create_sse_generator(self, task_id: str):
        """Generate Server-Sent Events for a specific task"""
        if task_id not in self.task_queues:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"
            return
        
        queue = self.task_queues[task_id]
        
        try:
            # Send initial connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                try:
                    # Wait for message with timeout for keepalive
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    if message is None:  # End of stream signal
                        yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
                        break
                    
                    # Send message as SSE
                    yield f"data: {json.dumps(message)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE Generator error for task {task_id}: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
        finally:
            # Don't cleanup immediately - keep for potential chat
            logger.info(f"SSE stream ended for task {task_id}")
    
    async def send_message(self, task_id: str, message_type: str, content: str, **kwargs):
        """Send message to specific task stream"""
        if task_id in self.task_queues:
            message = {
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                **kwargs
            }
            try:
                await self.task_queues[task_id].put(message)
                logger.debug(f"Message sent to task {task_id}: {message_type}")
            except Exception as e:
                logger.error(f"Failed to send message to task {task_id}: {str(e)}")
    
    async def start_research_task(self, task_id: str, request: ResearchRequest, session_token: str):
        """Start research task in background"""
        try:
            # Update task status
            self.active_tasks[task_id]['status'] = 'running'
            user_db_message = {'role': 'user', 'content': request.task, 'created': int(time.time())}
            chat_messages = get_chat_messages(redis_client, session_token, last_n=None)
            # Send initial message
            await self.send_message(task_id, 'status', 'Research task started', task=request.task)
            
            # Create custom logs handler for SSE
            logs_handler = SSELogsHandler(self, task_id)
            
            # Configure MCP if enabled
            if request.mcp_enabled and request.mcp_configs:
                await self.setup_mcp(task_id, request)
            
            report_content = ""
            
            # Execute research based on type
            try:
                if request.report_type == "multi_agents":
                    await self.send_message(task_id, 'status', 'Starting multi-agent research...')
                    result = await run_research_task(
                        query=request.task,
                        websocket=logs_handler,
                        tone=Tone[request.tone],
                        headers=request.headers or {}
                    )
                    report_content = result.get("report", "") if isinstance(result, dict) else str(result)
                    
                elif request.report_type == ReportType.DetailedReport.value:
                    await self.send_message(task_id, 'status', 'Starting detailed research...')
                    researcher = DetailedReport(
                        query=request.task,
                        query_domains=request.query_domains,
                        report_type=request.report_type,
                        report_source=request.report_source,
                        source_urls=request.source_urls,
                        document_urls=request.document_urls,
                        tone=Tone[request.tone],
                        websocket=logs_handler,
                        headers=request.headers or {},
                        mcp_configs=request.mcp_configs if request.mcp_enabled else None,
                        mcp_strategy=request.mcp_strategy if request.mcp_enabled else None,
                    )
                    report_content = await researcher.run()
                    
                else:  # Basic Report
                    await self.send_message(task_id, 'status', 'Starting basic research...')
                    researcher = BasicReport(
                        query=request.task,
                        query_domains=request.query_domains,
                        report_type=request.report_type,
                        report_source=request.report_source,
                        source_urls=request.source_urls,
                        document_urls=request.document_urls,
                        tone=Tone[request.tone],
                        websocket=logs_handler,
                        config_path="default",
                        headers=request.headers or {},
                        mcp_configs=request.mcp_configs if request.mcp_enabled else None,
                        mcp_strategy=request.mcp_strategy if request.mcp_enabled else None,
                    )
                    report_content = await researcher.run()
                
                # Store the completed report
                self.task_results[task_id] = report_content
                
                # Send final report
                await self.send_message(task_id, 'report', report_content)
                await self.send_message(task_id, 'status', 'Research completed successfully')
                assistant_db_message = { 'role': 'assistant', 'content': report_content, 'created': int(time.time())}
                logger.info(assistant_db_message)
                add_chat_messages(redis_client, session_token, [user_db_message, assistant_db_message])

                # Create chat agent for post-research chat
                if request.report_type != "multi_agents" and report_content:
                    self.chat_agents[task_id] = ChatAgentWithMemory(
                        report_content, 
                        request.task, 
                        request.headers or {}
                    )
                    await self.send_message(task_id, 'status', 'Chat agent ready')
                
                # Update task status
                self.active_tasks[task_id]['status'] = 'completed'
                self.active_tasks[task_id]['completed_at'] = datetime.now()
                
            except Exception as research_error:
                logger.error(f"Research error for task {task_id}: {str(research_error)}")
                await self.send_message(task_id, 'error', f'Research failed: {str(research_error)}')
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(research_error)
            
            # Signal completion
            await self.task_queues[task_id].put(None)
            
        except Exception as e:
            logger.error(f"Task execution error for {task_id}: {str(e)}")
            await self.send_message(task_id, 'error', f'Task execution failed: {str(e)}')
            self.active_tasks[task_id]['status'] = 'failed'
            self.active_tasks[task_id]['error'] = str(e)
            await self.task_queues[task_id].put(None)
    
    async def setup_mcp(self, task_id: str, request: ResearchRequest):
        """Setup MCP configuration"""
        try:
            import os
            current_retriever = os.getenv("RETRIEVER", "tavily")
            if "mcp" not in current_retriever:
                os.environ["RETRIEVER"] = f"{current_retriever},mcp"
            
            os.environ["MCP_STRATEGY"] = request.mcp_strategy
            
            await self.send_message(
                task_id, 
                'mcp_init', 
                f"🔧 MCP enabled with strategy '{request.mcp_strategy}' and {len(request.mcp_configs)} server(s)"
            )
        except Exception as e:
            await self.send_message(task_id, 'error', f'MCP setup failed: {str(e)}')
    
    def cleanup_task(self, task_id: str):
        """Clean up task resources (but keep results and chat agents)"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['cleaned_at'] = datetime.now()
        self.task_queues.pop(task_id, None)
        logger.info(f"Cleaned up task {task_id}")
    
    async def chat_with_agent(self, task_id: str, message: str) -> str:
        """Chat with research agent"""
        if task_id not in self.chat_agents:
            return "No research context available. Please run research first."
        
        try:
            # Create a simple response handler
            response_handler = SimpleResponseHandler()
            await self.chat_agents[task_id].chat(message, response_handler)
            return response_handler.get_response()
        except Exception as e:
            logger.error(f"Chat error for task {task_id}: {str(e)}")
            return f"Chat error: {str(e)}"
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Get task information"""
        return self.active_tasks.get(task_id)
    
    def get_task_result(self, task_id: str) -> Optional[str]:
        """Get completed task result"""
        return self.task_results.get(task_id)


class SSELogsHandler:
    """Custom logs handler for SSE streaming"""
    
    def __init__(self, manager: SSEResearchManager, task_id: str):
        self.manager = manager
        self.task_id = task_id
    
    async def send_json(self, data: dict):
        """Send JSON data through SSE"""
        message_type = data.get('type', 'log')
        content = data.get('content', data.get('message', ''))
        
        # Filter out some data keys for cleaner SSE
        extra_data = {k: v for k, v in data.items() 
                     if k not in ['type', 'content', 'message']}
        
        await self.manager.send_message(
            self.task_id,
            message_type,
            content,
            **extra_data
        )
    
    async def send_text(self, text: str):
        """Send text through SSE"""
        await self.manager.send_message(self.task_id, 'log', text)


class SimpleResponseHandler:
    """Simple response handler for chat"""
    
    def __init__(self):
        self.response = ""
    
    async def send_json(self, data: dict):
        if data.get('type') in ['chat', 'response']:
            self.response = data.get('content', data.get('message', ''))
    
    async def send_text(self, text: str):
        self.response = text
    
    def get_response(self) -> str:
        return self.response or "No response received"


# Initialize manager
research_manager = SSEResearchManager()

# FastAPI app setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SSE Research API")
    yield
    # Shutdown
    logger.info("Shutting down SSE Research API")

app = FastAPI(
    title="SSE Research API",
    description="Real-time research streaming with Server-Sent Events",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.post("/research/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start research task and return task ID for streaming"""
    task_id = research_manager.generate_task_id()
    session_token = "123456"
    if not chat_exists(redis_client, session_token):
        created = int(time.time())
        create_chat(redis_client, session_token, created)
    # Initialize task
    research_manager.active_tasks[task_id] = {
        'status': 'initialized',
        'request': request.dict(),
        'created_at': datetime.now(),
        'task_id': task_id
    }
    research_manager.task_queues[task_id] = asyncio.Queue()
    
    # Start research in background
    background_tasks.add_task(research_manager.start_research_task, task_id, request, session_token)
    
    return {
        "task_id": task_id, 
        "stream_url": f"/research/stream/{task_id}",
        "status": "initialized"
    }

@app.get("/research/stream/{task_id}")
async def stream_research(task_id: str):
    """Stream research progress via Server-Sent Events"""
    if task_id not in research_manager.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return StreamingResponse(
        research_manager.create_sse_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.post("/research/chat/{task_id}")
async def chat_with_research(task_id: str, request: ChatRequest):
    """Chat with research agent"""
    if task_id not in research_manager.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = await research_manager.chat_with_agent(task_id, request.message)
    return {"task_id": task_id, "response": response}

@app.get("/research/status/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    task_info = research_manager.get_task_info(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_info

@app.get("/research/result/{task_id}")
async def get_task_result(task_id: str):
    """Get completed task result"""
    result = research_manager.get_task_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task result not found")
    return {"task_id": task_id, "result": result}

@app.get("/research/tasks")
async def list_active_tasks():
    """List all active tasks"""
    return {
        "active_tasks": [
            {
                "task_id": task_id,
                "status": info.get('status'),
                "created_at": info.get('created_at'),
                "task": info.get('request', {}).get('task', 'Unknown')
            }
            for task_id, info in research_manager.active_tasks.items()
        ],
        "total": len(research_manager.active_tasks)
    }

@app.delete("/research/task/{task_id}")
async def cleanup_task(task_id: str):
    """Manually cleanup a task"""
    if task_id not in research_manager.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    research_manager.cleanup_task(task_id)
    return {"message": f"Task {task_id} cleaned up"}

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "running",
        "message": "SSE Research API is running",
        "endpoints": {
            "start_research": "/research/start",
            "stream": "/research/stream/{task_id}",
            "chat": "/research/chat/{task_id}",
            "status": "/research/status/{task_id}",
            "result": "/research/result/{task_id}",
            "tasks": "/research/tasks"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")