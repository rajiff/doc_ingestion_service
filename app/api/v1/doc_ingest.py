from fastapi import (
    APIRouter,
    Depends, File, Form,
    UploadFile, HTTPException, status
)
from app.core.dependency_factory import get_pdf_ingestion_service
from app.services.pdf_ingestion_service import PDFIngestionService
from app.schemas.doc_ingestion import DocIngestionResponse
from app.core.logger import logger

router = APIRouter()

@router.post("/ingest", response_model=DocIngestionResponse)
async def ingest_pdf(
    file: UploadFile = File(
        ..., description="Binary PDF file upload"),
    client_doc_id: str = Form(
        ..., description="Unique client-provided document identifier"),
    force_reingest: bool = Form(
        False, description="Overwrites existing index if True"),
    ingestion_service: PDFIngestionService = Depends(get_pdf_ingestion_service)
):
    """
    Endpoint to submit a valid PDF file for ingestion process
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF files are supported."
        )

    logger.info("Received request to ingest file %s with doc id %s",
           file.filename,
           client_doc_id)

    try:
        # Pass the stream directly (file.file) to prevent buffering giant files into RAM
        response = await ingestion_service.ingest_document(
            file_stream=file.file,
            client_doc_id=client_doc_id,
            force_reingest=force_reingest
        )

        logger.info("Completed ingestion of document of doc id %s with status %s",
                    client_doc_id,
                    response.status)

        return response
    except Exception as ex:
        logger.error("Error %s ingesting document: %s of id %s",
                     str(ex),
                     file.filename,
                     client_doc_id)
        # In a production app, you'd want more specific error handling
        # and logging here (e.g., parser errors vs system errors)
        raise HTTPException(status_code=500, detail=str(ex)) from ex
