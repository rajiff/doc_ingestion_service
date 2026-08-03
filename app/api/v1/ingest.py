from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.ingestion_service import IngestionService
from app.schemas.doc_ingestion import DocIngestionResponse

router = APIRouter()
# Instantiate service (singleton-like behavior for the dependency)
ingestion_service = IngestionService()

@router.post("/ingest", response_model=DocIngestionResponse)
async def ingest_document(file: UploadFile):
    """
    Endpoint to upload a PDF file and receive extracted text page-by-page.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Read file into memory
        content = await file.read()
        
        # Process via service
        result = await ingestion_service.ingest_document(
            file_bytes=content,
            filename=file.filename
        )
        
        return result

    except Exception as e:
        # In a production app, you'd want more specific error handling 
        # and logging here (e.g., parser errors vs system errors)
        raise HTTPException(status_code=500, detail=str(e))
