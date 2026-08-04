from fastapi import APIRouter
from app.api.v1 import ingest

# Aggregate all v1 routers
api_router = APIRouter()
api_router.include_router(ingest.router, tags=["Ingestion"])
