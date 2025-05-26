from __future__ import annotations

import logging
import os
import sys

from pathlib import Path

from dotenv import load_dotenv

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True, parents=True)

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import os

    # Set console encoding to UTF-8 for Windows
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Try to set console code page to UTF-8
    try:
        import subprocess

        subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
    except Exception:
        pass  # Ignore if chcp fails


# Configure logging with proper encoding
class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that safely handles Unicode characters."""

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Fall back to ASCII representation if Unicode fails
            try:
                msg: str = self.format(record)
                # Replace problematic Unicode characters with ASCII equivalents
                safe_msg: str = msg.encode("ascii", "replace").decode("ascii")
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                # Last resort: just skip the problematic log message
                pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File handler for general application logs with UTF-8 encoding
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        # Safe stream handler for console output
        SafeStreamHandler()
    ]
)

# Suppress verbose fontTools logging
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib').setLevel(logging.WARNING)

# Create logger instance
logger: logging.Logger = logging.getLogger(__name__)

load_dotenv()

from backend.server.server import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    from typing import Any, cast

    # Get all uvicorn configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    timeout_keep_alive = int(os.getenv("TIMEOUT_KEEP_ALIVE", "300"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    access_log = os.getenv("ACCESS_LOG", "true").lower() == "true"
    proxy_headers = os.getenv("PROXY_HEADERS", "true").lower() == "true"
    server_header = os.getenv("SERVER_HEADER", "true").lower() == "true"
    date_header = os.getenv("DATE_HEADER", "true").lower() == "true"
    forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "*")
    root_path = os.getenv("ROOT_PATH", "")
    backlog = int(os.getenv("BACKLOG", "2048"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    reload_delay = float(os.getenv("RELOAD_DELAY", "0.25"))
    ws_max_size = int(os.getenv("WS_MAX_SIZE", "16777216"))
    ws_ping_interval = float(os.getenv("WS_PING_INTERVAL", "20"))
    ws_ping_timeout = float(os.getenv("WS_PING_TIMEOUT", "20"))
    ws_per_message_deflate = os.getenv("WS_PER_MESSAGE_DEFLATE", "true").lower() == "true"

    # SSL configuration
    ssl_keyfile = os.getenv("SSL_KEYFILE", "") or None
    ssl_certfile = os.getenv("SSL_CERTFILE", "") or None
    ssl_keyfile_password = os.getenv("SSL_KEYFILE_PASSWORD", "") or None
    ssl_ca_certs = os.getenv("SSL_CA_CERTS", "") or None
    ssl_ciphers = os.getenv("SSL_CIPHERS", "TLSv1")

    # Optional parameters
    limit_concurrency = os.getenv("LIMIT_CONCURRENCY", "")
    if limit_concurrency and limit_concurrency.lower() != "null":
        limit_concurrency = int(limit_concurrency)
    else:
        limit_concurrency = None

    limit_max_requests = os.getenv("LIMIT_MAX_REQUESTS", "")
    if limit_max_requests and limit_max_requests.lower() != "null":
        limit_max_requests = int(limit_max_requests)
    else:
        limit_max_requests = None

    logger.info(f"Starting server on {host}:{port} with {workers} workers...")

    # Build configuration dictionary for uvicorn
    config = {
        "app": app,
        "host": host,
        "port": port,
        "workers": workers if workers > 1 else None,
        "timeout_keep_alive": timeout_keep_alive,
        "log_level": log_level,
        "access_log": access_log,
        "proxy_headers": proxy_headers,
        "server_header": server_header,
        "date_header": date_header,
        "forwarded_allow_ips": forwarded_allow_ips,
        "backlog": backlog,
        "ws_max_size": ws_max_size,
        "ws_ping_interval": ws_ping_interval,
        "ws_ping_timeout": ws_ping_timeout,
        "ws_per_message_deflate": ws_per_message_deflate,
    }

    # Add optional parameters only if they have values
    if root_path:
        config["root_path"] = root_path
    if reload:
        config["reload"] = reload
        config["reload_delay"] = reload_delay
    if limit_concurrency is not None:
        config["limit_concurrency"] = limit_concurrency
    if limit_max_requests is not None:
        config["limit_max_requests"] = limit_max_requests

    # Add SSL config if certificates are provided
    if ssl_keyfile and ssl_certfile:
        config["ssl_keyfile"] = ssl_keyfile
        config["ssl_certfile"] = ssl_certfile
        if ssl_keyfile_password:
            config["ssl_keyfile_password"] = ssl_keyfile_password
        if ssl_ca_certs:
            config["ssl_ca_certs"] = ssl_ca_certs
        config["ssl_ciphers"] = ssl_ciphers

    # Run the server with all configured parameters
    uvicorn.run(**cast(Any, config))

    logger.info("Server successfully started")
