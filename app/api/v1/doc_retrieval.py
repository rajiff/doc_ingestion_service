from fastapi import (
    APIRouter,
    Depends,
    HTTPException, status
)
from app.core.dependency_factory import get_pdf_retrieval_service
from app.services.pdf_retrieval_service import PDFRetrievalService
from app.schemas.doc_retrieval import DocQueryRequest, DocQueryResponse
from app.core.logger import logger

router = APIRouter()

@router.post("/retrieve_context", response_model=DocQueryResponse)
async def retrieve_context(
    request: DocQueryRequest,
    retrieval_service: PDFRetrievalService = Depends(get_pdf_retrieval_service)
):
    """
    Endpoint to execute vector similarity search on child chunks
    and reconstruct stitched parent context for LLM generation.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter must be a non-empty string."
        )

    try:
        response = await retrieval_service.retrieve_context(request)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        ) from val_err
    except Exception as ex:
        logger.error("Error handling retrieval request: %s", str(ex))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ex)
        ) from ex
