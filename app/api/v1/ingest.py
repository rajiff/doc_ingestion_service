import logging
from fastapi import APIRouter, UploadFile, HTTPException, Query
from app.core.config import ParserType
from app.services.ingestion_service import IngestionService
from app.schemas.doc_ingestion import DocIngestionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate service (singleton-like behavior for the dependency)
ingestion_service = IngestionService()

@router.post("/ingest", response_model=DocIngestionResponse)
async def ingest_document(
    file: UploadFile,
    parser_type: ParserType | None = Query(None)
):
    """
    Endpoint to upload a PDF file and receive extracted text page-by-page.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    logger.info(
        "Processing ingestion request for file: %s", 
        file.filename,
        extra={"extra": {"parser_engine": parser_type}}
    )

    try:
        # Read file into memory
        content = await file.read()

        # Process via service
        result = await ingestion_service.ingest_document(
            file_bytes=content,
            filename=file.filename,
            parser_type=parser_type
        )

        logger.info(
            "Successfully extracted document: %s", 
            file.filename,
            extra={"extra": {"total_pages": len(result.pages)}}
        )

        return result

    except Exception as ex:
        # In a production app, you'd want more specific error handling
        # and logging here (e.g., parser errors vs system errors)
        raise HTTPException(status_code=500, detail=str(ex))
