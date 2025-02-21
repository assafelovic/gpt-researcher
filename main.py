from __future__ import annotations

import logging

from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # File handler for general application logs
        logging.FileHandler("logs/app.log"),
        # Stream handler for console output
        logging.StreamHandler(),
    ],
)

# Create logs directory if it doesn't exist
logs_dir: Path = Path("logs")
logs_dir.mkdir(exist_ok=True, parents=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # File handler for general application logs
        logging.FileHandler("logs/app.log"),
        # Stream handler for console output
        logging.StreamHandler(),
    ],
)

# Suppress verbose fontTools logging
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
logging.getLogger("fontTools.ttLib").setLevel(logging.WARNING)

# Create logger instance
logger: logging.Logger = logging.getLogger(__name__)

from backend.server.server import app  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

if __name__ == "__main__":
    import uvicorn

    port = 8000
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
