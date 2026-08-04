import sys
import os
import requests
from loguru import logger
from app.core.config import settings

def init_logger():
    """Initialize logger for the app."""
    # Remove default handler
    logger.remove()

    # 1. Console Sink (Human Readable)
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        enqueue=True,
    )

    # Ensure log directory exists before attaching file sink
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 2. Rolling File Sink (Rotates at 10 MB, keeps logs for 7 days)
    logger.add(
        settings.LOG_FILE_PATH,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level=settings.LOG_LEVEL,
        serialize=True,     # Formats as JSON for machine parsing
        enqueue=True,       # Thread/async safe background writing
        backtrace=True,
        diagnose=True,
    )

    # 3. Direct Loki Sink (Non-blocking HTTP Push)
    if settings.LOKI_URL:
        def send_to_loki(message):
            try:
                record = message.record
                payload = {
                    "streams": [
                        {
                            "stream": {
                                "application": settings.PROJECT_NAME,
                                "level": record["level"].name.lower(),
                            },
                            "values": [
                                [
                                    str(int(record["time"].timestamp() * 1e9)),
                                    record["message"],
                                ]
                            ],
                        }
                    ]
                }
                # Keep timeout short (0.5s) to avoid blocking log threads
                requests.post(settings.LOKI_URL, json=payload, timeout=0.5)
            except Exception:
                # Silently catch all connection errors to protect stdout and file sinks
                pass

        # Note: Do not use enqueue=True on custom function sinks if they handle internal calls,
        # or catch exceptions cleanly inside the sink wrapper.
        logger.add(send_to_loki, level=settings.LOG_LEVEL, catch=True)

    return logger
