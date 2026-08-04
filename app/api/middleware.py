import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.access")

class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware that measures request latency and emits structured access logs 
    including duration_ms, status_code, and client IP.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip health check and metrics endpoints to keep logs clean
        if request.url.path in ("/metrics", "/health", "/docs", "/openapi.json"):
            return await call_next(request)

        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            status_code = 500
            raise exc from None
        finally:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            client_ip = request.client.host if request.client else "unknown"

            logger.info(
                "%s %s - %d (%s ms)",
                request.method,
                request.url.path,
                status_code,
                process_time_ms,
                extra={
                    "extra": {
                        "client_ip": client_ip,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": process_time_ms,
                    }
                },
            )