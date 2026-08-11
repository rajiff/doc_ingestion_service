from fastapi import APIRouter
from app.api.v1 import doc_ingest

# Aggregate all v1 routers
api_router = APIRouter()
api_router.include_router(doc_ingest.router, tags=["Ingestion"])
