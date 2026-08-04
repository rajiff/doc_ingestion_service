import sys
import requests
from loguru import logger
from app.core.config import settings

def init_logger():
    """initialize logger for the app"""
    # Remove default handler
    logger.remove()

    # 1. Console Sink (Human Readable)
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 2. Rolling File Sink (Rotates at 10 MB, keeps logs for 7 days)
    logger.add(
        settings.LOG_FILE_PATH,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level=settings.LOG_LEVEL,
        serialize=True,  # Formats as JSON for machine parsing
    )

    # 3. Direct Loki Sink (Custom HTTP Push Sink)
    if settings.LOKI_URL:
        def send_to_loki(message):
            record = message.record
            payload = {
                "streams": [
                    {
                        "stream": {
                            "application": settings.PROJECT_NAME,
                            "level": record["level"].name.lower(),
                        },
                        "values": [
                            [str(int(record["time"].timestamp() * 1e9)),
                             record["message"]]
                        ],
                    }
                ]
            }
            try:
                requests.post(settings.LOKI_URL, json=payload, timeout=2)
            except Exception:
                pass  # Avoid crashing app if Loki is temporarily unreachable

        logger.add(send_to_loki, level=settings.LOG_LEVEL)

    return logger
