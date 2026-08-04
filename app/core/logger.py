import json
import logging
import logging.handlers
import os
import sys
import time
from queue import Queue
import requests
from app.core.config import settings

# Global reference to prevent garbage collection of the background listener
_queue_listener: logging.handlers.QueueListener | None = None

class JSONFormatter(logging.Formatter):
    """Formats Python log records into structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Unpack extra dict if passed via extra={"extra": {...}} or extra={...}
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_object.update(record.extra)

        return json.dumps(log_object)


class NonBlockingLokiHandler(logging.Handler):
    """Direct HTTP Push Handler for Grafana Loki."""

    def __init__(self, loki_url: str, app_name: str):
        super().__init__()
        self.loki_url = loki_url
        self.app_name = app_name

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)
            ts_ns = str(int(time.time() * 1e9))

            payload = {
                "streams": [
                    {
                        "stream": {
                            "application": self.app_name,
                            "level": record.levelname.lower(),
                        },
                        "values": [[ts_ns, log_entry]],
                    }
                ]
            }
            requests.post(self.loki_url, json=payload, timeout=0.5)
        except Exception:
            pass


def init_logger():
    """Configures non-blocking, asynchronous structured JSON logging."""
    global _queue_listener

    # Stop previous listener if re-initialized
    if _queue_listener is not None:
        _queue_listener.stop()

    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    json_formatter = JSONFormatter()
    target_handlers = []

    # 1. Console Handler (Human-readable stdout)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    stdout_handler.setFormatter(stdout_formatter)
    target_handlers.append(stdout_handler)

    # 2. File Handler (JSON output)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    target_handlers.append(file_handler)

    # 3. Loki Handler
    if settings.LOKI_URL:
        loki_handler = NonBlockingLokiHandler(
            loki_url=settings.LOKI_URL, app_name=settings.PROJECT_NAME
        )
        loki_handler.setFormatter(json_formatter)
        target_handlers.append(loki_handler)

    # 4. Async Queue Setup
    log_queue: Queue = Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    _queue_listener = logging.handlers.QueueListener(
        log_queue, *target_handlers, respect_handler_level=True
    )
    _queue_listener.start()

    # 5. Explicitly Configure Root AND 'app' Loggers
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [queue_handler]

    # FORCE 'app' namespace to catch all app code logs and route to queue
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.handlers = [queue_handler]
    app_logger.propagate = False

    # Force Uvicorn loggers to use our queue_handler
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        uv_logger = logging.getLogger(name)
        uv_logger.setLevel(log_level)
        uv_logger.handlers = [queue_handler]
        uv_logger.propagate = False


    return root_logger