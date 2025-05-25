from __future__ import annotations

import logging
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # File handler for general application logs (with UTF-8 encoding)
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        # Safe stream handler for console output
        SafeStreamHandler(),
    ],
)

# Suppress verbose fontTools logging
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
logging.getLogger("fontTools.ttLib").setLevel(logging.WARNING)

# Create logger instance
logger = logging.getLogger(__name__)

load_dotenv()

from backend.server.server import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
