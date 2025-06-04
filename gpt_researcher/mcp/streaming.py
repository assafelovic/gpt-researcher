"""
MCP Streaming Utilities Module

Handles websocket streaming and logging for MCP operations.
"""
import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPStreamer:
    """
    Handles streaming output for MCP operations.
    
    Responsible for:
    - Streaming logs to websocket
    - Synchronous/asynchronous logging
    - Error handling in streaming
    """

    def __init__(self, websocket=None):
        """
        Initialize the MCP streamer.
        
        Args:
            websocket: WebSocket for streaming output
        """
        self.websocket = websocket

    async def stream_log(self, message: str, data: Any = None):
        """Stream a log message to the websocket if available."""
        logger.info(message)
        
        if self.websocket:
            try:
                from ..actions.utils import stream_output
                await stream_output(
                    type="logs", 
                    content="mcp_retriever", 
                    output=message, 
                    websocket=self.websocket,
                    metadata=data
                )
            except Exception as e:
                logger.error(f"Error streaming log: {e}")
                
    def stream_log_sync(self, message: str, data: Any = None):
        """Synchronous version of stream_log for use in sync contexts."""
        logger.info(message)
        
        if self.websocket:
            try:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.stream_log(message, data))
                    else:
                        loop.run_until_complete(self.stream_log(message, data))
                except RuntimeError:
                    logger.debug("Could not stream log: no running event loop")
            except Exception as e:
                logger.error(f"Error in sync log streaming: {e}")

    async def stream_stage_start(self, stage: str, description: str):
        """Stream the start of a research stage."""
        await self.stream_log(f"🔧 {stage}: {description}")

    async def stream_stage_complete(self, stage: str, result_count: int = None):
        """Stream the completion of a research stage."""
        if result_count is not None:
            await self.stream_log(f"✅ {stage} completed: {result_count} results")
        else:
            await self.stream_log(f"✅ {stage} completed")

    async def stream_tool_selection(self, selected_count: int, total_count: int):
        """Stream tool selection information."""
        await self.stream_log(f"🧠 Using LLM to select {selected_count} most relevant tools from {total_count} available")

    async def stream_tool_execution(self, tool_name: str, step: int, total: int):
        """Stream tool execution progress."""
        await self.stream_log(f"🔍 Executing tool {step}/{total}: {tool_name}")

    async def stream_research_results(self, result_count: int, total_chars: int = None):
        """Stream research results summary."""
        if total_chars:
            await self.stream_log(f"✅ MCP research completed: {result_count} results obtained ({total_chars:,} chars)")
        else:
            await self.stream_log(f"✅ MCP research completed: {result_count} results obtained")

    async def stream_error(self, error_msg: str):
        """Stream error messages."""
        await self.stream_log(f"❌ {error_msg}")

    async def stream_warning(self, warning_msg: str):
        """Stream warning messages."""
        await self.stream_log(f"⚠️ {warning_msg}")

    async def stream_info(self, info_msg: str):
        """Stream informational messages."""
        await self.stream_log(f"ℹ️ {info_msg}") 