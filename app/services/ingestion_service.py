from app.interfaces.base_parser import BasePDFParser
from app.parsers.pypdf_parser import PyPDFParser
from app.schemas.doc_ingestion import (
    DocIngestionMetadata,
    DocIngestionResponse,
    DocPageExtraction,
)

class IngestionService:
    """Orchestrates the parser strategy and sanitization of extracted content."""

    def __init__(self):
        # Default to PyPDFParser, but this can be easily extended to support
        # different strategies based on configuration or file type.
        self.parser: BasePDFParser = PyPDFParser()

    async def ingest_document(
            self,
            file_bytes: bytes,
            filename: str) -> DocIngestionResponse:
        """Processes a raw PDF byte stream and returns structured extraction results."""
        # Perform extraction
        extracted_pages = self.parser.extract_text(file_bytes)

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
