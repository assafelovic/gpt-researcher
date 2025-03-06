from __future__ import annotations

import argparse
import logging
import ssl

from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn

from backend.server.server import app
from dotenv import load_dotenv

if TYPE_CHECKING:
    import os

    from fastapi import FastAPI


def configure_logging(
    log_file: os.PathLike | str = "logs/app.log",
) -> logging.Logger:
    """Configures the application logging.

    Args:
        log_file: Path to the log file.

    Returns:
        Configured logger instance.
    """
    # Create logs directory if it doesn't exist
    logs_dir: Path = Path("logs")
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # File handler for general application logs
            logging.FileHandler(log_file),
            # Stream handler for console output
            logging.StreamHandler(),
        ],
    )

    # Suppress verbose fontTools logging
    logging.getLogger("fontTools").setLevel(logging.WARNING)
    logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
    logging.getLogger("fontTools.ttLib").setLevel(logging.WARNING)

    # Create logger instance
    from gpt_researcher.utils.logger import get_formatted_logger

    logger: logging.Logger = get_formatted_logger(__name__)
    return logger


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run the GPT Researcher application.")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to run the server on.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to run the server on.")
    parser.add_argument("--choose", "-c", action="store_true", help="Choose a configuration to run.")
    parser.add_argument("--interactive", "-i", action="store_true", help="Choose a configuration to run.")
    parser.add_argument("--frontend", type=str, default="default", help="Frontend to use (default or other).")
    parser.add_argument("--uds", type=str, default=None, help="Unix domain socket.")
    parser.add_argument("--fd", type=int, default=None, help="File descriptor.")
    parser.add_argument("--loop", type=str, default="auto", help="Event loop implementation.")
    parser.add_argument("--http", type=str, default="auto", help="HTTP protocol implementation.")
    parser.add_argument("--ws", type=str, default="auto", help="WebSocket protocol implementation.")
    parser.add_argument("--ws-max-size", type=int, default=16777216, help="WebSocket maximum message size.")
    parser.add_argument("--ws-max-queue", type=int, default=32, help="WebSocket maximum queue size.")
    parser.add_argument("--ws-ping-interval", type=float, default=20, help="WebSocket ping interval.")
    parser.add_argument("--ws-ping-timeout", type=float, default=20, help="WebSocket ping timeout.")
    parser.add_argument("--ws-per-message-deflate", type=bool, default=True, help="Enable WebSocket per-message deflate.")
    parser.add_argument("--lifespan", type=str, default="auto", help="Lifespan protocol implementation.")
    parser.add_argument("--interface", type=str, default="auto", help="Application interface.")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload.")
    parser.add_argument("--reload-dirs", type=str, default=None, help="Directories to watch for changes.")
    parser.add_argument("--reload-includes", type=str, default=None, help="Files to include for reloading.")
    parser.add_argument("--reload-excludes", type=str, default=None, help="Files to exclude from reloading.")
    parser.add_argument("--reload-delay", type=float, default=0.25, help="Delay before reloading.")
    parser.add_argument("--workers", type=int, default=None, help="Number of worker processes.")
    parser.add_argument("--env-file", type=str, default=None, help="Path to environment file.")
    parser.add_argument(
        "--log-config", type=str, default=None, help="Path to logging configuration file."
    )  # Simplified to str
    parser.add_argument("--log-level", type=str, default=None, help="Logging level.")
    parser.add_argument("--access-log", action="store_true", help="Enable access logging.")
    parser.add_argument("--proxy-headers", action="store_true", help="Enable proxy headers.")
    parser.add_argument("--server-header", action="store_true", help="Enable server header.")
    parser.add_argument("--date-header", action="store_true", help="Enable date header.")
    parser.add_argument("--forwarded-allow-ips", type=str, default=None, help="Allowed IPs for forwarded headers.")
    parser.add_argument("--root-path", type=str, default="", help="ASGI root path.")
    parser.add_argument("--limit-concurrency", type=int, default=None, help="Maximum concurrent connections.")
    parser.add_argument("--backlog", type=int, default=2048, help="Maximum connection backlog.")
    parser.add_argument("--limit-max-requests", type=int, default=None, help="Maximum number of requests.")
    parser.add_argument("--timeout-keep-alive", type=int, default=5, help="Keep-alive timeout.")
    parser.add_argument("--timeout-graceful-shutdown", type=int, default=None, help="Graceful shutdown timeout.")
    parser.add_argument("--ssl-keyfile", type=str, default=None, help="Path to SSL key file.")
    parser.add_argument("--ssl-certfile", type=str, default=None, help="Path to SSL certificate file.")
    parser.add_argument("--ssl-keyfile-password", type=str, default=None, help="Password for SSL key file.")
    parser.add_argument(
        "--ssl-version", type=int, default=ssl.PROTOCOL_TLS, help="SSL protocol version."
    )  # Use default from ssl
    parser.add_argument("--ssl-cert-reqs", type=int, default=ssl.CERT_NONE, help="SSL certificate requirements.")
    parser.add_argument("--ssl-ca-certs", type=str, default=None, help="Path to CA certificates.")
    parser.add_argument("--ssl-ciphers", type=str, default="TLSv1", help="SSL ciphers.")
    parser.add_argument("--headers", type=str, default=None, help="Custom headers.")  # Simplified to str for easier input
    parser.add_argument("--use-colors", action="store_true", help="Enable colored logging output.")  # store_true is simpler
    parser.add_argument("--app-dir", type=str, default=None, help="Application directory.")
    parser.add_argument("--factory", action="store_true", help="Use application factory.")
    parser.add_argument(
        "--h11-max-incomplete-event-size", type=int, default=None, help="Maximum incomplete event size for h11."
    )

    return parser.parse_args()


def run_uvicorn(
    args: argparse.Namespace,
    app: FastAPI,
    logger: logging.Logger,
) -> None:
    """Runs the Uvicorn server with the provided arguments.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
        app: The application to run.
    """

    logger.info(f"Starting server listening on {args.host}:{args.port}...")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        lifespan=args.lifespan,
        interface=args.interface,
        reload=args.reload,
        reload_dirs=args.reload_dirs,
        reload_includes=args.reload_includes,
        reload_excludes=args.reload_excludes,
        reload_delay=args.reload_delay,
        workers=args.workers,
        env_file=args.env_file,
        log_config=args.log_config,
        log_level=args.log_level,
        access_log=args.access_log,
        proxy_headers=args.proxy_headers,
        server_header=args.server_header,
        date_header=args.date_header,
        forwarded_allow_ips=args.forwarded_allow_ips,
        root_path=args.root_path,
        limit_concurrency=args.limit_concurrency,
        backlog=args.backlog,
        limit_max_requests=args.limit_max_requests,
        timeout_keep_alive=args.timeout_keep_alive,
        timeout_graceful_shutdown=args.timeout_graceful_shutdown,
        ssl_version=args.ssl_version,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile_password=args.ssl_keyfile_password,
        ssl_cert_reqs=args.ssl_cert_reqs,
        ssl_ca_certs=args.ssl_ca_certs,
        ssl_ciphers=args.ssl_ciphers,
        headers=args.headers,
        use_colors=args.use_colors,
        app_dir=args.app_dir,
        factory=args.factory,
        h11_max_incomplete_event_size=args.h11_max_incomplete_event_size,
    )


def main():
    logger: logging.Logger = configure_logging()
    load_dotenv()
    args: argparse.Namespace = parse_arguments()
    run_uvicorn(args, app, logger)


if __name__ == "__main__":
    main()
