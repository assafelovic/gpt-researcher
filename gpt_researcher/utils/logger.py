from __future__ import annotations

import logging
import multiprocessing
import os
import sys
import threading

from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Generator, Literal


from loggerplus.utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from io import TextIOWrapper
    from multiprocessing.process import BaseProcess
    from types import TracebackType

# Global lock for thread-safe operations (from file_context_0) :-)
LOGGING_LOCK = threading.Lock()
THREAD_LOCAL = threading.local()
THREAD_LOCAL.is_logging = False


@contextmanager
def logging_context() -> Generator[None, Any, None]:
    global LOGGING_LOCK  # noqa: PLW0602
    with LOGGING_LOCK:
        prev_state: bool = getattr(THREAD_LOCAL, "is_logging", False)
        THREAD_LOCAL.is_logging = True
    try:
        yield
    finally:
        with LOGGING_LOCK:
            THREAD_LOCAL.is_logging = prev_state


class CustomExceptionFormatter(logging.Formatter):
    sep = f"{os.linesep}----------------------------------------------------------------{os.linesep}"

    def formatException(
        self,
        ei: tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None],
    ) -> str:
        etype: type[BaseException] | None
        value: BaseException | None
        tb: TracebackType | None
        etype, value, tb = ei
        if value is None:
            return self.sep + super().formatException(ei) + self.sep
        return self.sep + format_exception_with_variables(value, etype=etype, tb=tb) + self.sep

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        result = super().format(record)
        # if record.exc_info:
        #    result += f"{os.linesep}{self.formatException(record.exc_info)}"
        return result


TRACE_LOG_LEVEL: int = 5


def get_formatted_logger(
    name: str | None = None,
    log_dir: Path | None = None,
    propagate: bool = True,
) -> logging.Logger:
    logger: logging.Logger = logging.getLogger() if name is None else logging.getLogger(name)
    if not logger.handlers:
        use_level: int = logging.INFO
        logger.setLevel(use_level)

        cur_process: BaseProcess = multiprocessing.current_process()
        console_format_str = "%(levelname)s(%(name)s): %(message)s"
        if cur_process.name == "MainProcess":
            log_dir = Path("logs") if log_dir is None else log_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            everything_log_file = "debug.log"
            info_warning_log_file = "info.log"
            error_critical_log_file = "errors.log"
            exception_log_file = "exception.log"
        else:
            log_dir = Path(f"logs/{cur_process.pid}") if log_dir is None else log_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            everything_log_file: str = f"debug_{cur_process.pid}.log"
            info_warning_log_file: str = f"info_{cur_process.pid}.log"
            error_critical_log_file: str = f"errors_{cur_process.pid}.log"
            exception_log_file: str = f"exception_{cur_process.pid}.log"
            console_format_str: str = f"PID={cur_process.pid} - {console_format_str}"

        console_handler = ColoredConsoleHandler()
        formatter = logging.Formatter(console_format_str)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Redirect stdout and stderr
        sys.stdout = CustomPrintToLogger(logger, sys.__stdout__, log_type="stdout")  # type: ignore[assignment]
        sys.stderr = CustomPrintToLogger(logger, sys.__stderr__, log_type="stderr")  # type: ignore[assignment]

        default_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        exception_formatter = CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Handler for everything (DEBUG and above)
        if use_level == logging.DEBUG:
            log_dir.mkdir(parents=True, exist_ok=True)

            Path(log_dir / everything_log_file).parent.mkdir(parents=True, exist_ok=True)
            everything_handler = RotatingFileHandler(
                str(log_dir / everything_log_file), maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf8"
            )
            everything_handler.setLevel(logging.DEBUG)
            everything_handler.setFormatter(default_formatter)
            logger.addHandler(everything_handler)

        # Handler for INFO and WARNING
        Path(log_dir / info_warning_log_file).parent.mkdir(parents=True, exist_ok=True)
        info_warning_handler = RotatingFileHandler(
            str(log_dir / info_warning_log_file), maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf8"
        )
        info_warning_handler.setLevel(logging.INFO)
        info_warning_handler.setFormatter(default_formatter)
        info_warning_handler.addFilter(LogLevelFilter(logging.ERROR, reject=True))
        logger.addHandler(info_warning_handler)

        # Handler for ERROR and CRITICAL
        Path(log_dir / error_critical_log_file).parent.mkdir(parents=True, exist_ok=True)
        error_critical_handler = RotatingFileHandler(
            str(log_dir / error_critical_log_file), maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf8"
        )
        error_critical_handler.setLevel(logging.ERROR)
        error_critical_handler.addFilter(LogLevelFilter(logging.ERROR))
        error_critical_handler.setFormatter(default_formatter)
        logger.addHandler(error_critical_handler)

        # Handler for EXCEPTIONS (using CustomExceptionFormatter)
        Path(log_dir / exception_log_file).parent.mkdir(parents=True, exist_ok=True)
        exception_handler = RotatingFileHandler(
            str(log_dir / exception_log_file), maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf8"
        )
        exception_handler.setLevel(logging.ERROR)
        exception_handler.addFilter(LogLevelFilter(logging.ERROR))
        exception_handler.setFormatter(exception_formatter)
        logger.addHandler(exception_handler)

        # Set propagation based on parameter
        logger.propagate = propagate

    else:
        # If handlers already exist, just update the propagate flag
        logger.propagate = propagate

    return logger


class LogLevelFilter(logging.Filter):
    """Filters (allows) all the log messages at or above a specific level."""

    def __init__(
        self,
        passlevel: int,
        *,
        reject: bool = False,
    ):
        super().__init__()
        self.passlevel: int = passlevel
        self.reject: bool = reject

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        if self.reject:
            return record.levelno < self.passlevel
        return record.levelno >= self.passlevel


class UTF8StreamWrapper:
    def __init__(self, original_stream: TextIOWrapper):
        self.original_stream: TextIOWrapper = original_stream

    def write(self, message: str):
        # Ensure message is a string, encode to UTF-8 with errors replaced,
        # then write to the original stream's buffer directly.
        # This fixes/works-around a bug in Python's logging module, observed in 3.8.10
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        if isinstance(message, str):
            message_bytes: bytes = message.encode("utf-8", errors="replace")
        self.original_stream.buffer.write(message_bytes)

    def flush(self):
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        self.original_stream.flush()

    def __getattr__(self, attr: str) -> Any:
        # Delegate any other method calls to the original stream
        return getattr(self.original_stream, attr)


class CustomPrintToLogger:
    """Redirect stdout and stderr to logger."""

    def __init__(
        self,
        logger: logging.Logger,
        original: TextIOWrapper,
        log_type: Literal["stdout", "stderr"] = "stdout",
    ) -> None:
        self.logger: logging.Logger = logger
        self.original_out: TextIOWrapper = original
        self.log_type: Literal["stdout", "stderr"] = log_type
        self.configure_logger_stream()
        self.buffer: str = ""

    def isatty(self) -> Literal[False]:
        return False

    def configure_logger_stream(self):
        utf8_wrapper = UTF8StreamWrapper(self.original_out)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(utf8_wrapper)  # type: ignore[arg-type]

    def write(self, message: str):
        if getattr(THREAD_LOCAL, "is_logging", False):
            self.original_out.write(message)
        else:
            self.buffer += message
            while os.linesep in self.buffer:  # HACK: might have nuanced bugs, but it works for now.
                line, self.buffer = self.buffer.split(os.linesep, 1)
                self._log_message(line)

    def flush(self):
        if self.buffer:
            self._log_message(self.buffer)
            self.buffer = ""

    def _log_message(self, message: str):
        if message and message.strip():
            with logging_context():
                if self.log_type == "stderr":
                    self.logger.warning(message.strip())
                else:
                    self.logger.debug(message.strip())


class ColoredConsoleHandler(logging.StreamHandler):
    try:
        import colorama  # type: ignore[import-untyped, reportMissingModuleSource]

        colorama.init()
        USING_COLORAMA = True
    except ImportError:
        USING_COLORAMA = False

    RESET_CODE: str = colorama.Style.RESET_ALL if USING_COLORAMA else "\033[0m"
    COLOR_CODES: ClassVar[dict[int, str]] = {
        TRACE_LOG_LEVEL: colorama.Fore.BLUE if USING_COLORAMA else "\033[0;34m",  # Blue
        logging.DEBUG: colorama.Fore.CYAN if USING_COLORAMA else "\033[0;36m",  # Cyan
        logging.INFO: colorama.Fore.WHITE if USING_COLORAMA else "\033[0;37m",  # White
        logging.WARNING: colorama.Fore.YELLOW if USING_COLORAMA else "\033[0;33m",  # Yellow
        logging.ERROR: colorama.Fore.RED if USING_COLORAMA else "\033[0;31m",  # Red
        logging.CRITICAL: colorama.Back.RED if USING_COLORAMA else "\033[1;41m",  # Red background
    }

    def format(self, record: logging.LogRecord) -> str:
        return f"{self.COLOR_CODES.get(record.levelno, '')}{super().format(record)}{self.RESET_CODE}"


class DefaultFormatter(ColoredConsoleHandler):
    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()  # pragma: no cover
