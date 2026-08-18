from fastapi import APIRouter
from app.api.v1 import doc_ingest, doc_retrieval

# Aggregate all v1 routers
api_router = APIRouter()
api_router.include_router(doc_ingest.router, prefix="/documents", tags=["Ingestion"])
api_router.include_router(doc_retrieval.router, prefix="/documents", tags=["Retrieval"])
