"""Logging configuration for the standalone application."""

from __future__ import annotations

import sys

from pathlib import Path

from loguru import logger


def setup_logging(log_path: str | Path | None = None) -> None:
    """Configure loguru logger with console and file outputs.

    Args:
        log_path: Optional path to store log files. If None, logs will only go to console.
    """
    # Remove default handler
    logger.remove()

    # Add colored console handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        enqueue=True,  # Thread-safe logging
        diagnose=True,  # Show variables in tracebacks
        backtrace=True,  # Show full traceback
    )

    # Add file handler if log path is provided
    if log_path:
        log_file = Path(log_path) / "gpt_researcher_{time}.log"
        logger.add(
            str(log_file),
            rotation="50 MB",  # Rotate when file reaches 50MB
            retention="1 week",  # Keep logs for 1 week
            compression="zip",  # Compress rotated logs
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            enqueue=True,
            diagnose=True,
            backtrace=True,
        )

def get_logger(name: str) -> Logger:
    """Get a logger instance with the given name.

    Args:
        name: Name for the logger, typically __name__

    Returns:
        A loguru logger instance bound with the given name
    """
    return logger.bind(name=name)