from fastapi import FastAPI
from app.api.v1 import api_router as v1_router

app = FastAPI(title="PDF Ingestion Service", description="Service for extracting text from PDF documents")

# Include the V1 API routes
app.include_router(v1_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint to verify service availability.
    """
    return {"status": "healthy"}
