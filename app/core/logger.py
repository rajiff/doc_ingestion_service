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
    Pushes structured JSON payloads over HTTP.
    """

    def __init__(self, loki_url: str, app_name: str):
        super().__init__()
        self.loki_url = loki_url
        self.app_name = app_name

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)
            # Timestamp in nanoseconds required by Loki API
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
            # Short timeout to prevent network stalls
            requests.post(self.loki_url, json=payload, timeout=0.5)
        except Exception:
            # Silently handle Loki downtime to protect other sinks
            print("Exception occurred while pushing logs to Loki. ")
        return


def init_logger():
    """
    Configures non-blocking, asynchronous structured JSON logging
    using standard library QueueHandler & QueueListener.
    """
    # 1. Ensure log directory exists
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

    # Handler C: Loki Sink (Optional HTTP Push)
    if settings.LOKI_URL:
        loki_handler = NonBlockingLokiHandler(
            loki_url=settings.LOKI_URL, app_name=settings.PROJECT_NAME
        )
        loki_handler.setFormatter(json_formatter)
        target_handlers.append(loki_handler)

    # 2. Setup Async Queue Listener (Offloads disk & network I/O from FastAPI threads)
    log_queue = Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    queue_listener = logging.handlers.QueueListener(
        log_queue, *target_handlers, respect_handler_level=True
    )
    queue_listener.start()

    # 3. Apply Queue Handler to Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    root_logger.handlers = [queue_handler]

    # 4. Standardize Uvicorn and FastAPI loggers
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers = [queue_handler]

    return root_logger
