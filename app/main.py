from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.core.logger import init_logger, logger
from app.core.telemetry import setup_telemetry
from app.api.v1 import api_router as v1_router

# Initialize Application & Loguru Logger
init_logger()
logger.info(f"Service instance started with settings: {settings.model_dump()}")

app = FastAPI(title=settings.PROJECT_NAME,
              description=settings.PROJECT_DESC)

# Set up OTel Auto-Instrumentation
setup_telemetry(app)

# Prometheus Exporter for RED Metrics
Instrumentator().instrument(app).expose(app)

# Include the V1 API routes
app.include_router(v1_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint to verify service availability."""
    return {"status": "healthy"}
