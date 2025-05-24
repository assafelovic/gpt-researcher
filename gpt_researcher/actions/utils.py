from __future__ import annotations

from typing import Any, Callable

from fastapi import WebSocket

from gpt_researcher.utils.logger import get_formatted_logger

logger = get_formatted_logger()


async def stream_output(
    output_type: str,
    content: str,
    output: str,
    websocket: WebSocket | None = None,
    output_log: bool = True,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Streams output to the websocket.

    Args:
        output_type(str): The type of output.
        content(str): The content of the output.
        output(str): The output to stream.
        websocket(Any): The websocket to stream the output to.
        output_log(bool): Whether to log the output.
        metadata(dict[str, Any]): The metadata of the output.

    Returns:
        None
    """
    if (not websocket or output_log) and output_type != "images":
        try:
            logger.info(f"{output}")
        except UnicodeEncodeError:
            # Option 1: Replace problematic characters with a placeholder
            logger.error(output.encode("cp1252", errors="replace").decode("cp1252"))

    if websocket:
        await websocket.send_json({"type": output_type, "content": content, "output": output, "metadata": metadata})


async def safe_send_json(websocket: WebSocket, data: dict[str, Any]) -> None:
    """Safely send JSON data through a WebSocket connection.

    Args:
        websocket(WebSocket): The WebSocket connection to send data through.
        data(dict[str, Any]): The data to send as JSON.

    Returns:
        None
    """
    try:
        await websocket.send_json(data)
    except Exception as e:
        logger.error(f"Error sending JSON through WebSocket: {e}")


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> float:
    """Calculate the cost of API usage based on the number of tokens and the model used.

    Args:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        model (str): The model used for the API call.

    Returns:
        float: The calculated cost in USD.
    """
    # Define cost per 1k tokens for different models
    costs: dict[str, float] = {
        "gpt-3.5-turbo": 0.002,
        "gpt-4": 0.03,
        "gpt-4-32k": 0.06,
        # Add more models and their costs as needed
    }

    model = model.lower()
    if model not in costs:
        logger.warning(f"Unknown model: {model}. Cost calculation may be inaccurate.")
        return 0.0

    cost_per_1k: float = costs[model]
    total_tokens: int = prompt_tokens + completion_tokens
    return (total_tokens / 1000) * cost_per_1k


def format_token_count(count: int) -> str:
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
    websocket: WebSocket,
) -> None:
    """Update and send the cost information through the WebSocket.

    Args:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        model (str): The model used for the API call.
        websocket (WebSocket): The WebSocket connection to send data through.
    """
    cost: float = calculate_cost(prompt_tokens, completion_tokens, model)
    total_tokens: int = prompt_tokens + completion_tokens

    await safe_send_json(
        websocket,
        {
            "type": "cost",
            "data": {
                "total_tokens": format_token_count(total_tokens),
                "prompt_tokens": format_token_count(prompt_tokens),
                "completion_tokens": format_token_count(completion_tokens),
                "total_cost": f"${cost:.4f}",
            },
        },
    )


def create_cost_callback(websocket: WebSocket) -> Callable:
    """Create a callback function for updating costs.

    Args:
        websocket (WebSocket): The WebSocket connection to send data through.

    Returns:
        Callable: A callback function that can be used to update costs.
    """

    async def cost_callback(prompt_tokens: int, completion_tokens: int, model: str) -> None:
        await update_cost(prompt_tokens, completion_tokens, model, websocket)

    return cost_callback
