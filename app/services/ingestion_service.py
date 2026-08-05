import logging
from app.core.config import ParserType
from app.api.deps import get_parser
from app.interfaces import BasePDFParser
from app.schemas import (
    DocIngestionMetadata,
    DocIngestionResponse,
    DocPageExtraction,
)

class IngestionService:
    """Orchestrates the parser strategy and sanitization of extracted content."""

    def __init__(self):
        """Initializes the service with a default parser strategy."""

    async def ingest_document(
            self,
            file_bytes: bytes,
            filename: str,
            parser_type: ParserType | None) -> DocIngestionResponse:
        """Processes a raw PDF byte stream and returns structured extraction results."""

        parser: BasePDFParser = get_parser(parser_type)
        logging.info(
            "Processing file %s", 
            filename,
            extra={"extra": {"parser_engine": parser.__class__.__name__}}
        )
        # Perform extraction
        extracted_pages = parser.extract_text(file_bytes)

        # Prepare data for response
        pages = [
            DocPageExtraction(page_number=p["page_number"], text=p["text"])
            for p in extracted_pages
        ]

        metadata = DocIngestionMetadata(
            filename=filename,
            parser_used="pypdf",
            total_pages=len(pages)
        )

        return DocIngestionResponse(
            metadata=metadata,
            pages=pages
        )
