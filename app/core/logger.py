import json
import logging
import logging.handlers
import os
import sys
import time

from queue import Queue
import requests

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Formats Python log records into structured JSON. Thread-safe for QueueHandler."""

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module or "",
            "function": record.funcName or "",
            "line": record.lineno,
        }

        # Catch exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Include custom extra metadata passed via extra={"extra": {...}}
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_object.update(record.extra)

        return json.dumps(log_object)


class NonBlockingLokiHandler(logging.Handler):
    """
    Direct HTTP Push Handler for Grafana Loki.
    Pushes structured JSON payloads over HTTP asynchronously via thread pool.
    """

    def __init__(self, loki_url: str, app_name: str):
        super().__init__()
        self.loki_url = loki_url
        self.app_name = app_name
        # Use ThreadPoolExecutor for async processing to avoid blocking main thread
        from concurrent.futures import ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._queue: list = []  # Internal queue for buffered logs

    def emit(self, record: logging.LogRecord):
        try:
            # Format log entry using standard formatter
            log_entry = self.format(record)

            # Build Loki payload - timestamps in nanoseconds
            ts_ns = str(int(time.time() * 1e9))

            payload = {
                "streams": [
                    {
                        "stream": {
                            "job": self.app_name,  # Use 'job' instead of 'application' for Loki
                            "level": record.levelname.lower(),  # Loki expects lowercase levels
                        },
                        "values": [[ts_ns, log_entry]],  # [timestamp, label_message]
                    }
                ]
            }

            # Submit to thread pool for async processing
            self._executor.submit(self._send_to_loki, payload)
        except Exception as e:
            # Log the exception but don't crash main logging flow
            import sys
            print(f"Loki Handler error: {e}", file=sys.stderr)

    def _send_to_loki(self, payload: dict):
        """Actual HTTP POST to Loki - runs in background thread."""
        try:
            requests.post(self.loki_url, json=payload, timeout=5.0)
        except Exception:
            # Silently handle Loki downtime
            pass

    def shutdown(self):
        """Flush pending logs on shutdown."""
        try:
            for payload in self._queue:
                self._send_to_loki(payload)
            self._executor.shutdown(wait=True)
        except Exception:
            pass


def init_basic_logger():
    """Simple standard logger that outputs clean logs to stdout.

    WARNING: This is a basic function that should NOT be used with QueueHandler
    when queue-based async logging is desired. Use init_logger() instead.
    """
    logging.basicConfig(
        stream=sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
        force=True,
    )
    logger = logging.getLogger("app")
    # Attach a simple handler since basicConfig doesn't guarantee proper attachment
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


def init_logger():
    """
    Configures non-blocking, asynchronous structured JSON logging
    using standard library QueueHandler & QueueListener.

    Sets up:
    1. Console handler (human-readable format)
    2. File handler (JSON format for log aggregation)
    3. Loki handler (async HTTP push if configured)
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    json_formatter = JSONFormatter()
    target_handlers = []

    # Handler A: Console stdout (Human-readable for terminal)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    stdout_handler.setFormatter(stdout_formatter)
    target_handlers.append(stdout_handler)

    # Handler B: Rolling File Sink (JSON output)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    target_handlers.append(file_handler)

    # Handler C: Loki Sink (Optional HTTP Push via async thread pool)
    if settings.LOKI_URL:
        loki_handler = NonBlockingLokiHandler(
            loki_url=settings.LOKI_URL, app_name=settings.PROJECT_NAME
        )
        loki_handler.setFormatter(json_formatter)
        target_handlers.append(loki_handler)

    # Setup Queue Listener (Offloads disk & network I/O from FastAPI threads)
    log_queue = Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_listener = logging.handlers.QueueListener(
        log_queue, *target_handlers, respect_handler_level=True
    )
    queue_listener.start()

    # Apply Queue Handler to Root Logger - THIS IS THE SINGLE LOGGING PIPELINE
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    root_logger.handlers = [queue_handler]

    # Standardize Uvicorn and FastAPI loggers to use the SAME queue handler
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        uv_logger = logging.getLogger(logger_name)
        # Replace handlers so they all funnel through the same queue
        if uv_logger.handlers:
            uv_logger.handlers = [queue_handler]

    return root_logger
