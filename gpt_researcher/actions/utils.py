from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litellm.cost_calculator import cost_per_token

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from backend.server.server_utils import CustomLogsHandler
    from fastapi.websockets import WebSocket

logger: logging.Logger = get_formatted_logger()


async def stream_output(
    output_type: str,
    content: str,
    output: str,
    websocket: WebSocket | CustomLogsHandler | None = None,
    output_log: bool = True,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Streams output to the websocket.

    Args:
        type (str): The type of output to stream.
        content (str): The content to stream.
        output (str): The output to stream.
        websocket (WebSocket | CustomLogsHandler | None): The websocket to stream to.
        output_log (bool): Whether to log the output.
        metadata (dict[str, Any] | None): The metadata to stream.
    """
    if (not websocket or output_log) and output_type != "images":
        try:
            logger.info(str(output))
        except UnicodeEncodeError:
            logger.exception(output.encode("cp1252", errors="replace").decode("cp1252"))

    # For research content, send as research_progress to enable real-time streaming
    if output_type == "research" and content == "content":
        await safe_send_json(websocket, {"type": "research_progress", "content": output, "metadata": metadata})
    # For subquery context windows, send as research_progress for real-time streaming
    elif output_type == "logs" and content == "subquery_context_window":
        await safe_send_json(websocket, {"type": "research_progress", "content": output, "metadata": metadata})
    # For all other logs content, ensure it's sent as logs type for proper frontend handling
    elif output_type == "logs":
        await safe_send_json(websocket, {"type": "logs", "content": content, "output": output, "metadata": metadata})
    else:
        await safe_send_json(websocket, {"type": "logs", "content": content, "output": output, "metadata": metadata})


async def safe_send_json(
    websocket: WebSocket | CustomLogsHandler | None,
    data: dict[str, Any],
) -> None:
    """Safely send JSON data through a WebSocket connection.

    Args:
        websocket (WebSocket | CustomLogsHandler | None): The WebSocket connection to send data through.
        data (dict[str, Any]): The data to send as JSON.
    """
    if websocket is None:
        logger.warning("WebSocket is None, skipping send_json")
        return

    try:
        await websocket.send_json(data)
    except Exception as e:
        logger.exception(f"Error sending JSON through WebSocket: {e.__class__.__name__}: {e}")


def format_token_count(
    count: int,
) -> str:
    """Format the token count with commas for better readability.

    Args:
        count (int): The token count to format.

    Returns:
        str: The formatted token count.
    """
    return f"{count:,}"


async def update_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    websocket: WebSocket | CustomLogsHandler | None,
):
    """Update and send the cost information through the WebSocket.

    Args:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        model (str): The model used for the API call.
        websocket (WebSocket | CustomLogsHandler | None): The WebSocket connection to send data through.
    """
    prompt_tokens_cost, completion_tokens_cost = cost_per_token(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    combined_costs: float = prompt_tokens_cost + completion_tokens_cost
    total_tokens: int = prompt_tokens + completion_tokens

    await safe_send_json(
        websocket,
        {
            "type": "cost",
            "data": {
                "total_tokens": format_token_count(total_tokens),
                "prompt_tokens": format_token_count(prompt_tokens),
                "completion_tokens": format_token_count(completion_tokens),
                "prompt_tokens_cost": f"${prompt_tokens_cost:.4f}",
                "completion_tokens_cost": f"${completion_tokens_cost:.4f}",
                "total_cost": f"${combined_costs:.4f}",
            },
        },
    )
