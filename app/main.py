from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.core.logger import init_logger
# from app.core.logger import init_basic_logger
from app.core.telemetry import setup_telemetry
# from app.api.middleware import AccessLogMiddleware
from app.api.v1 import api_router as v1_router

# init_basic_logger()

# Initialize once at startup
logger = init_logger()  # Returns root logger with all handlers configured
logger.propagate = True

app = FastAPI(title=settings.PROJECT_NAME,
              description=settings.PROJECT_DESC)

# Set up OTel Auto-Instrumentation
setup_telemetry(app)

# Prometheus Exporter for RED Metrics
Instrumentator().instrument(app).expose(app)

# Register Custom Access Log Middleware
# app.add_middleware(AccessLogMiddleware)

# Include the V1 API routes
app.include_router(v1_router, prefix="/api/v1")

logger.info("Message from logger")
logger.error("Error message", extra={"extra_field": "value"})

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint to verify service availability."""
    return {"status": "healthy"}
