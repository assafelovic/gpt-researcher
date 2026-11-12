import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load .env first so it can configure logging and the server below.
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
    print(f"Unknown LOG_LEVEL {LOG_LEVEL!r}, using INFO")
    LOG_LEVEL = "INFO"
# Set LOG_TO_FILE=false to log to the console only (e.g. in containers).
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").strip().lower() not in ("0", "false", "no", "off")
# An unset or empty LOG_DIR falls back to logs/ next to this file.
LOG_DIR = Path(os.getenv("LOG_DIR") or Path(__file__).resolve().parent / "logs")

handlers: list[logging.Handler] = [logging.StreamHandler()]

if LOG_TO_FILE:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                LOG_DIR / "app.log",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
        )
    except OSError as e:
        # e.g. read-only filesystem: keep running with console logging only.
        print(f"File logging disabled, cannot write to {LOG_DIR}: {e}")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers,
)

# Suppress verbose fontTools logging
for name in ("fontTools", "fontTools.subset", "fontTools.ttLib"):
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Imported after load_dotenv() so the app sees .env values at import time.
from backend.server.app import app  # noqa: E402

if __name__ == "__main__":
    # Defaults to localhost; set HOST=0.0.0.0 to expose on the network (Docker does this).
    host = os.getenv("HOST", "127.0.0.1")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        sys.exit(f"Invalid PORT {os.getenv('PORT')!r}: must be a number, e.g. PORT=8000")

    logger.info(f"Starting server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level=LOG_LEVEL.lower())
