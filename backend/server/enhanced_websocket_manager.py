from __future__ import annotations

import asyncio
import datetime
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from backend.chat import ChatAgentWithMemory
from backend.report_type import BasicReport, DetailedReport
from backend.server.server_utils import CustomLogsHandler
from gpt_researcher.actions import stream_output
from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task


class ConnectionStatus(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    PROCESSING = "processing"
    SUSPENDED = "suspended"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    PING = "ping"
    PONG = "pong"
    RESEARCH = "research"
    CHAT = "chat"
    STATUS = "status"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class ConnectionMetrics:
    """Track connection health and performance metrics"""

    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    messages_sent: int = 0
    messages_received: int = 0
    errors_count: int = 0
    avg_response_time: float = 0.0
    ping_latency: float = 0.0
    total_uptime: float = 0.0
    reconnection_count: int = 0


@dataclass
class QueuedMessage:
    """Represents a message in the processing queue"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.RESEARCH
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Higher number = higher priority
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 300.0  # 5 minutes default timeout
    websocket_id: Optional[str] = None


@dataclass
class ConnectionState:
    """Comprehensive connection state management"""

    websocket: WebSocket
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    chat_agent: Optional[ChatAgentWithMemory] = None
    current_task: Optional[str] = None
    message_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    sender_task: Optional[asyncio.Task] = None
    processor_task: Optional[asyncio.Task] = None
    last_ping_time: float = 0.0
    client_info: Dict[str, Any] = field(default_factory=dict)
    rate_limit_tokens: int = 100  # Rate limiting
    rate_limit_window: float = 60.0  # 1 minute window


class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with resilience, security, and monitoring"""

    def __init__(
        self,
        max_connections: int = 100,
        heartbeat_interval: float = 30.0,
        message_timeout: float = 300.0,
        max_message_size: int = 1024 * 1024,  # 1MB
        enable_metrics: bool = True,
        log_level: str = "INFO",
    ):
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.message_timeout = message_timeout
        self.max_message_size = max_message_size
        self.enable_metrics = enable_metrics

        # Connection management
        self.active_connections: Dict[str, ConnectionState] = {}
        self.connection_by_websocket: Dict[WebSocket, str] = {}
        self.message_queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()

        # Background tasks
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.queue_processor_task: Optional[asyncio.Task] = None
        self.metrics_collector_task: Optional[asyncio.Task] = None

        # Security and rate limiting
        self.blocked_ips: Set[str] = set()
        self.rate_limit_cache: Dict[str, List[float]] = {}

        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))

    async def start_background_tasks(self):
        """Start all background maintenance tasks"""
        if not self.heartbeat_task or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        if not self.queue_processor_task or self.queue_processor_task.done():
            self.queue_processor_task = asyncio.create_task(
                self._queue_processor_loop()
            )

        if self.enable_metrics and (
            not self.metrics_collector_task or self.metrics_collector_task.done()
        ):
            self.metrics_collector_task = asyncio.create_task(
                self._metrics_collector_loop()
            )

    async def stop_background_tasks(self):
        """Stop all background tasks gracefully"""
        tasks = [
            self.heartbeat_task,
            self.queue_processor_task,
            self.metrics_collector_task,
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def connect(self, websocket: WebSocket, client_host: str = "") -> str:
        """Enhanced connection handling with security checks"""

        # Security checks
        if len(self.active_connections) >= self.max_connections:
            self.logger.warning(
                f"Connection limit reached, rejecting connection from {client_host}"
            )
            await websocket.close(code=1013, reason="Server overloaded")
            raise ConnectionError("Maximum connections exceeded")

        if client_host in self.blocked_ips:
            self.logger.warning(f"Blocked IP attempted connection: {client_host}")
            await websocket.close(code=1008, reason="IP blocked")
            raise ConnectionError("IP address blocked")

        # Rate limiting check
        if not self._check_rate_limit(client_host):
            self.logger.warning(f"Rate limit exceeded for {client_host}")
            await websocket.close(code=1008, reason="Rate limit exceeded")
            raise ConnectionError("Rate limit exceeded")

        try:
            await websocket.accept()

            # Create connection state
            connection_state = ConnectionState(websocket=websocket)
            connection_state.client_info = {
                "host": client_host,
                "user_agent": websocket.headers.get("user-agent", ""),
                "connected_at": datetime.datetime.now().isoformat(),
            }

            # Store connection mappings
            connection_id = connection_state.connection_id
            self.active_connections[connection_id] = connection_state
            self.connection_by_websocket[websocket] = connection_id

            # Start sender task for this connection
            connection_state.sender_task = asyncio.create_task(
                self._connection_sender_loop(connection_state)
            )

            # Update status
            connection_state.status = ConnectionStatus.CONNECTED

            # Start background tasks if not running
            await self.start_background_tasks()

            self.logger.info(f"WebSocket connected: {connection_id} from {client_host}")

            # Send connection confirmation
            await self._send_system_message(
                connection_state,
                {
                    "type": "connection_established",
                    "connection_id": connection_id,
                    "server_time": datetime.datetime.now().isoformat(),
                },
            )

            return connection_id

        except Exception as e:
            self.logger.error(f"Error accepting WebSocket connection: {e}")
            await websocket.close(code=1011, reason="Internal server error")
            raise

    async def disconnect(
        self, websocket: WebSocket, code: int = 1000, reason: str = "Normal closure"
    ):
        """Enhanced disconnection with cleanup"""

        connection_id = self.connection_by_websocket.get(websocket)
        if not connection_id:
            self.logger.warning("Attempting to disconnect unknown WebSocket")
            return

        connection_state = self.active_connections.get(connection_id)
        if not connection_state:
            return

        try:
            connection_state.status = ConnectionStatus.DISCONNECTING

            # Cancel sender task
            if connection_state.sender_task and not connection_state.sender_task.done():
                connection_state.sender_task.cancel()
                try:
                    await connection_state.sender_task
                except asyncio.CancelledError:
                    pass

            # Update metrics
            if self.enable_metrics:
                connection_state.metrics.total_uptime = (
                    time.time() - connection_state.metrics.connected_at
                )

            # Close WebSocket
            try:
                await websocket.close(code=code, reason=reason)
            except Exception as e:
                self.logger.debug(f"Error closing WebSocket: {e}")

            # Clean up
            self.active_connections.pop(connection_id, None)
            self.connection_by_websocket.pop(websocket, None)

            connection_state.status = ConnectionStatus.DISCONNECTED

            self.logger.info(
                f"WebSocket disconnected: {connection_id}, reason: {reason}"
            )

        except Exception as e:
            self.logger.error(f"Error during WebSocket disconnection: {e}")

    async def handle_message(self, websocket: WebSocket, message: str):
        """Enhanced message handling with validation and queuing"""

        connection_id = self.connection_by_websocket.get(websocket)
        if not connection_id:
            self.logger.warning("Message from unknown WebSocket")
            return

        connection_state = self.active_connections.get(connection_id)
        if not connection_state:
            return

        # Update activity time
        connection_state.metrics.last_activity = time.time()
        connection_state.metrics.messages_received += 1

        # Validate message size
        if len(message) > self.max_message_size:
            self.logger.warning(
                f"Message too large from {connection_id}: {len(message)} bytes"
            )
            await self._send_error_message(connection_state, "Message too large")
            return

        try:
            # Handle ping specially for low latency
            if message.strip() == "ping":
                connection_state.last_ping_time = time.time()
                await self._send_immediate_message(connection_state, "pong")
                return

            # Parse and validate message
            if message.startswith("start "):
                # Research request
                try:
                    payload = json.loads(message[6:])  # Remove "start "
                    await self._queue_research_request(connection_state, payload)
                except json.JSONDecodeError as e:
                    await self._send_error_message(
                        connection_state, f"Invalid JSON: {str(e)}"
                    )
                except Exception as e:
                    await self._send_error_message(
                        connection_state, f"Request error: {str(e)}"
                    )
            else:
                # Try to parse as JSON for other message types
                try:
                    parsed_message = json.loads(message)
                    await self._handle_parsed_message(connection_state, parsed_message)
                except json.JSONDecodeError:
                    # Handle simple text messages (like chat)
                    await self._queue_chat_message(connection_state, message)
                except Exception as e:
                    await self._send_error_message(
                        connection_state, f"Message processing error: {str(e)}"
                    )

        except Exception as e:
            self.logger.error(f"Error handling message from {connection_id}: {e}")
            connection_state.metrics.errors_count += 1
            await self._send_error_message(
                connection_state, "Internal processing error"
            )

    async def _queue_research_request(
        self, connection_state: ConnectionState, payload: Dict[str, Any]
    ):
        """Queue a research request for processing"""

        # Validate required fields
        if "task" not in payload:
            await self._send_error_message(
                connection_state, "Missing required field: task"
            )
            return

        # Sanitize payload to prevent information leakage
        sanitized_payload = self._sanitize_research_payload(payload)

        queued_message = QueuedMessage(
            type=MessageType.RESEARCH,
            payload=sanitized_payload,
            priority=2,  # High priority for research requests
            websocket_id=connection_state.connection_id,
            timeout=600.0,  # 10 minutes for research requests
        )

        await self.message_queue.put(queued_message)
        connection_state.status = ConnectionStatus.PROCESSING

        # Send acknowledgment
        await self._send_system_message(
            connection_state,
            {
                "type": "request_queued",
                "message_id": queued_message.id,
                "estimated_processing_time": "2-5 minutes",
            },
        )

    async def _queue_chat_message(
        self, connection_state: ConnectionState, message: str
    ):
        """Queue a chat message for processing"""

        queued_message = QueuedMessage(
            type=MessageType.CHAT,
            payload={"message": message},
            priority=1,  # Normal priority for chat
            websocket_id=connection_state.connection_id,
        )

        await self.message_queue.put(queued_message)

    async def _handle_parsed_message(
        self, connection_state: ConnectionState, message: Dict[str, Any]
    ):
        """Handle parsed JSON messages"""

        message_type = message.get("type", "unknown")

        if message_type == "status_request":
            await self._send_status_update(connection_state)
        elif message_type == "chat":
            await self._queue_chat_message(connection_state, message.get("content", ""))
        else:
            self.logger.warning(f"Unknown message type: {message_type}")

    def _sanitize_research_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize research payload to prevent sensitive information leakage"""

        # Create a copy to avoid modifying the original
        sanitized = payload.copy()

        # Remove or sanitize sensitive fields
        sensitive_fields = ["api_key", "token", "password", "secret", "auth"]
        for sensitive_field in sensitive_fields:
            if sensitive_field in sanitized:
                sanitized[sensitive_field] = "[REDACTED]"

        # Limit string lengths to prevent DoS
        max_lengths = {
            "task": 2000,
            "report_type": 50,
            "report_source": 100,
            "tone": 50,
        }

        for max_length_field, max_length in max_lengths.items():
            if max_length_field in sanitized and isinstance(
                sanitized[max_length_field], str
            ):
                sanitized[max_length_field] = sanitized[max_length_field][:max_length]

        return sanitized

    async def _send_immediate_message(
        self,
        connection_state: ConnectionState,
        message: str,
    ):
        """Send a message immediately without queueing"""
        try:
            if connection_state.websocket and connection_state.status not in {
                ConnectionStatus.DISCONNECTING,
                ConnectionStatus.DISCONNECTED,
            }:
                await connection_state.websocket.send_text(message)
                connection_state.metrics.messages_sent += 1
        except Exception as e:
            self.logger.error(
                f"Error sending immediate message: {e.__class__.__name__}: {e}"
            )

    async def _send_system_message(
        self, connection_state: ConnectionState, message: Dict[str, Any]
    ):
        """Send a system message to the client"""
        try:
            system_message = {
                "type": "system",
                "timestamp": datetime.datetime.now().isoformat(),
                **message,
            }
            await connection_state.message_queue.put(json.dumps(system_message))
        except Exception as e:
            self.logger.error(
                f"Error queuing system message: {e.__class__.__name__}: {e}"
            )

    async def _send_error_message(self, connection_state: ConnectionState, error: str):
        """Send an error message to the client"""
        try:
            error_message = {
                "type": "error",
                "error": error,
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await connection_state.message_queue.put(json.dumps(error_message))
        except Exception as e:
            self.logger.error(
                f"Error sending error message: {e.__class__.__name__}: {e}"
            )

    async def _send_status_update(self, connection_state: ConnectionState):
        """Send connection status update to client"""
        try:
            status_message = {
                "type": "status",
                "connection_id": connection_state.connection_id,
                "status": connection_state.status.value,
                "uptime": time.time() - connection_state.metrics.connected_at,
                "messages_sent": connection_state.metrics.messages_sent,
                "messages_received": connection_state.metrics.messages_received,
                "queue_size": connection_state.message_queue.qsize(),
            }
            await connection_state.message_queue.put(json.dumps(status_message))
        except Exception as e:
            self.logger.error(
                f"Error sending status update: {e.__class__.__name__}: {e}"
            )

    async def _connection_sender_loop(self, connection_state: ConnectionState):
        """Message sender loop for a specific connection"""
        try:
            while (
                connection_state.status
                not in [ConnectionStatus.DISCONNECTING, ConnectionStatus.DISCONNECTED]
                and not connection_state.websocket.client_state.DISCONNECTED
            ):
                try:
                    # Wait for message or timeout
                    message = await asyncio.wait_for(
                        connection_state.message_queue.get(), timeout=1.0
                    )

                    if message is None:  # Shutdown signal
                        break

                    if connection_state.websocket:
                        await connection_state.websocket.send_text(message)
                        connection_state.metrics.messages_sent += 1

                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    self.logger.error(
                        f"Error in sender loop: {e.__class__.__name__}: {e}"
                    )
                    connection_state.metrics.errors_count += 1
                    break

        except Exception as e:
            self.logger.error(
                f"Fatal error in sender loop: {e.__class__.__name__}: {e}"
            )
        finally:
            self.logger.debug(f"Sender loop ended for {connection_state.connection_id}")

    async def _queue_processor_loop(self):
        """Process queued messages from all connections"""
        try:
            while True:
                try:
                    # Get message with timeout
                    queued_message = await asyncio.wait_for(
                        self.message_queue.get(), timeout=5.0
                    )

                    # Process message based on type
                    if queued_message.type == MessageType.RESEARCH:
                        await self._process_research_request(queued_message)
                    elif queued_message.type == MessageType.CHAT:
                        await self._process_chat_request(queued_message)

                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue
                except Exception as e:
                    self.logger.error(
                        f"Error processing queued message: {e.__class__.__name__}: {e}"
                    )

        except asyncio.CancelledError:
            self.logger.info("Queue processor loop cancelled")
        except Exception as e:
            self.logger.error(
                f"Fatal error in queue processor loop: {e.__class__.__name__}: {e}"
            )

    async def _process_research_request(self, queued_message: QueuedMessage):
        """Process a research request"""
        connection_state = self.active_connections.get(queued_message.websocket_id)
        if not connection_state:
            self.logger.warning(
                f"Connection not found for queued message: {queued_message.websocket_id}"
            )
            return

        try:
            payload = queued_message.payload

            # Create enhanced logs handler
            logs_handler = CustomLogsHandler(
                connection_state.websocket, payload.get("task", "")
            )

            # Extract parameters
            task = payload.get("task", "")
            report_type = payload.get("report_type", "research_report")
            report_source = payload.get("report_source", "web")
            source_urls = payload.get("source_urls", [])
            document_urls = payload.get("document_urls", [])
            tone = payload.get("tone", "objective")
            query_domains = payload.get("query_domains", [])

            # Convert tone to enum if it's a string
            if isinstance(tone, str):
                try:
                    tone = Tone[tone]
                except KeyError:
                    tone = Tone.Objective

            # Set current task
            connection_state.current_task = task

            # Process based on report type
            if report_type == "multi_agents":
                report = await run_research_task(
                    query=task,
                    websocket=logs_handler,
                    stream_output=stream_output,
                    tone=tone,
                    headers=None,
                )
                report_content = report.get("report", "")
            elif report_type == ReportType.DetailedReport.value:
                researcher = DetailedReport(
                    query=task,
                    query_domains=query_domains,
                    report_type=report_type,
                    report_source=report_source,
                    source_urls=source_urls,
                    document_urls=document_urls,
                    tone=tone,
                    config_path="default",
                    websocket=logs_handler,
                    headers=None,
                )
                report_content = await researcher.run()
            else:
                researcher = BasicReport(
                    query=task,
                    query_domains=query_domains,
                    report_type=report_type,
                    report_source=report_source,
                    source_urls=source_urls,
                    document_urls=document_urls,
                    tone=tone,
                    config_path="default",
                    websocket=logs_handler,
                    headers=None,
                )
                report_content = await researcher.run()

            # Create chat agent for follow-up questions
            connection_state.chat_agent = ChatAgentWithMemory(
                report_content, "default", None
            )

            # Update connection status
            connection_state.status = ConnectionStatus.READY
            connection_state.current_task = None

        except Exception as e:
            self.logger.error(
                f"Error processing research request: {e.__class__.__name__}: {e}"
            )
            await self._send_error_message(
                connection_state, f"Research processing failed: {str(e)}"
            )
            connection_state.status = ConnectionStatus.ERROR

    async def _process_chat_request(self, queued_message: QueuedMessage):
        """Process a chat message"""
        connection_state = self.active_connections.get(queued_message.websocket_id)
        if not connection_state:
            return

        try:
            message = queued_message.payload.get("message", "")

            if connection_state.chat_agent:
                await connection_state.chat_agent.chat(
                    message, connection_state.websocket
                )
            else:
                await self._send_error_message(
                    connection_state,
                    "No research context available. Please run a research task first.",
                )

        except Exception as e:
            self.logger.error(
                f"Error processing chat request: {e.__class__.__name__}: {e}"
            )
            await self._send_error_message(
                connection_state, f"Chat processing failed: {str(e)}"
            )

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all connections"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                # Clean up disconnected connections
                disconnected_ids = []

                for connection_id, connection_state in self.active_connections.items():
                    try:
                        if connection_state.websocket.client_state.DISCONNECTED:
                            disconnected_ids.append(connection_id)
                            continue

                        # Check for stale connections
                        time_since_activity = (
                            time.time() - connection_state.metrics.last_activity
                        )
                        if (
                            time_since_activity > self.heartbeat_interval * 3
                        ):  # 3x heartbeat interval
                            self.logger.warning(
                                f"Stale connection detected: {connection_id}"
                            )
                            disconnected_ids.append(connection_id)
                            continue

                        # Send ping
                        await self._send_immediate_message(connection_state, "ping")

                    except Exception as e:
                        self.logger.error(
                            f"Error in heartbeat for {connection_id}: {e.__class__.__name__}: {e}"
                        )
                        disconnected_ids.append(connection_id)

                # Clean up disconnected connections
                for connection_id in disconnected_ids:
                    connection_state = self.active_connections.get(connection_id)
                    if connection_state:
                        await self.disconnect(
                            connection_state.websocket, 1001, "Connection timeout"
                        )

        except asyncio.CancelledError as e:
            self.logger.info(f"Heartbeat loop cancelled: {e.__class__.__name__}: {e}")
        except Exception as e:
            self.logger.error(
                f"Fatal error in heartbeat loop: {e.__class__.__name__}: {e}"
            )

    async def _metrics_collector_loop(self):
        """Collect and log metrics periodically"""
        try:
            while True:
                await asyncio.sleep(60)  # Collect metrics every minute

                total_connections = len(self.active_connections)
                total_messages_sent = sum(
                    conn.metrics.messages_sent
                    for conn in self.active_connections.values()
                )
                total_messages_received = sum(
                    conn.metrics.messages_received
                    for conn in self.active_connections.values()
                )
                total_errors = sum(
                    conn.metrics.errors_count
                    for conn in self.active_connections.values()
                )

                self.logger.info(
                    f"Metrics - Connections: {total_connections}, "
                    f"Messages Sent: {total_messages_sent}, "
                    f"Messages Received: {total_messages_received}, "
                    f"Errors: {total_errors}, "
                    f"Queue Size: {self.message_queue.qsize()}"
                )

        except asyncio.CancelledError as e:
            self.logger.info(
                f"Metrics collector loop cancelled: {e.__class__.__name__}: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"Error in metrics collector loop: {e.__class__.__name__}: {e}"
            )

    def _check_rate_limit(self, client_host: str) -> bool:
        """Check if client is within rate limits"""
        current_time = time.time()

        # Clean old entries
        if client_host in self.rate_limit_cache:
            self.rate_limit_cache[client_host] = [
                t
                for t in self.rate_limit_cache[client_host]
                if current_time - t < 60  # Keep entries from last minute
            ]
        else:
            self.rate_limit_cache[client_host] = []

        # Check rate limit (max 10 connections per minute per IP)
        if len(self.rate_limit_cache[client_host]) >= 10:
            return False

        # Add current request
        self.rate_limit_cache[client_host].append(current_time)
        return True

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        total_connections = len(self.active_connections)

        if total_connections == 0:
            return {
                "total_connections": 0,
                "avg_uptime": 0,
                "total_messages": 0,
                "total_errors": 0,
            }

        current_time = time.time()

        stats = {
            "total_connections": total_connections,
            "max_connections": self.max_connections,
            "connections_by_status": {},
            "avg_uptime": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_errors": 0,
            "avg_latency": 0,
            "queue_size": self.message_queue.qsize(),
        }

        # Calculate detailed statistics
        uptime_sum = 0
        latency_sum = 0
        latency_count = 0

        for connection_state in self.active_connections.values():
            # Count by status
            status = connection_state.status.value
            stats["connections_by_status"][status] = (
                stats["connections_by_status"].get(status, 0) + 1
            )

            # Sum metrics
            uptime_sum += current_time - connection_state.metrics.connected_at
            stats["total_messages_sent"] += connection_state.metrics.messages_sent
            stats["total_messages_received"] += (
                connection_state.metrics.messages_received
            )
            stats["total_errors"] += connection_state.metrics.errors_count

            if connection_state.metrics.ping_latency > 0:
                latency_sum += connection_state.metrics.ping_latency
                latency_count += 1

        stats["avg_uptime"] = uptime_sum / total_connections
        stats["avg_latency"] = latency_sum / latency_count if latency_count > 0 else 0

        return stats

    @asynccontextmanager
    async def lifespan_context(self):
        """Context manager for managing WebSocket manager lifecycle"""
        try:
            await self.start_background_tasks()
            yield self
        finally:
            await self.stop_background_tasks()

            # Disconnect all active connections
            disconnect_tasks = []
            for connection_state in list(self.active_connections.values()):
                disconnect_tasks.append(
                    self.disconnect(connection_state.websocket, 1001, "Server shutdown")
                )

            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)

            self.logger.info("Enhanced WebSocket Manager shutdown complete")


# Backward compatibility with existing WebSocketManager
class WebSocketManager(EnhancedWebSocketManager):
    """Backward compatible wrapper for existing code"""

    def __init__(self):
        super().__init__()
        self.active_connections: List[WebSocket] = []  # Legacy compatibility
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}
        self.chat_agent: Optional[ChatAgentWithMemory] = None

    async def start_sender(self, websocket: WebSocket):
        """Legacy method for backward compatibility"""
        connection_id = self.connection_by_websocket.get(websocket)
        if connection_id:
            connection_state = self.active_connections.get(connection_id)
            if connection_state and connection_state.sender_task:
                await connection_state.sender_task

    async def connect(self, websocket: WebSocket) -> str:
        """Legacy connect method"""
        connection_id = await super().connect(websocket)

        # Maintain legacy list for compatibility
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)

        return connection_id

    async def disconnect(self, websocket: WebSocket):
        """Legacy disconnect method"""
        await super().disconnect(websocket)

        # Clean up legacy structures
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        self.sender_tasks.pop(websocket, None)
        self.message_queues.pop(websocket, None)

    async def start_streaming(
        self,
        task: str,
        report_type: str,
        report_source: str,
        source_urls: List[str],
        document_urls: List[str],
        tone: Tone | str,
        websocket: WebSocket,
        headers: Dict[str, str] | None = None,
        query_domains: List[str] | None = None,
        **kwargs,
    ) -> str:
        """Legacy streaming method"""

        # Create payload in new format
        payload = {
            "task": task,
            "report_type": report_type,
            "report_source": report_source,
            "source_urls": source_urls,
            "document_urls": document_urls,
            "tone": tone.value if isinstance(tone, Tone) else tone,
            "query_domains": query_domains or [],
            **kwargs,
        }

        # Queue research request
        connection_id = self.connection_by_websocket.get(websocket)
        if connection_id:
            connection_state = self.active_connections.get(connection_id)
            if connection_state:
                await self._queue_research_request(connection_state, payload)

                # Wait for completion (legacy behavior)
                while connection_state.status == ConnectionStatus.PROCESSING:
                    await asyncio.sleep(0.1)

                # Set chat agent for legacy compatibility
                self.chat_agent = connection_state.chat_agent

                return "Research completed"

        return "Research failed"

    async def chat(self, message: str, websocket: WebSocket):
        """Legacy chat method"""
        connection_id = self.connection_by_websocket.get(websocket)
        if connection_id:
            connection_state = self.active_connections.get(connection_id)
            if connection_state:
                await self._queue_chat_message(connection_state, message)
            else:
                # Legacy fallback
                await websocket.send_json(
                    {
                        "type": "chat",
                        "content": "Knowledge empty, please run the research first to obtain knowledge",
                    }
                )
        else:
            await websocket.send_json(
                {
                    "type": "chat",
                    "content": "Connection not found, please refresh and try again",
                }
            )
