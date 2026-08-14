import io
from typing import List

import pymupdf

from app.interfaces import BasePDFParser
from app.schemas.doc_ingestion import DocPageExtraction
from app.core.logger import logger

class PyMuPDFParser(BasePDFParser):
    """Concrete implementation of BasePDFParser using PyMuPDF.

    This parser uses PyMuPDF (fitz) library to extract text from PDF documents
    efficiently. It processes the entire document and returns page-level text
    chunks in a standardized format.
    """

    def extract_text(self, file_bytes: bytes) -> List[DocPageExtraction]:
        """Parses raw PDF bytes and extracts text chunked by page.

        Args:
            file_bytes: Raw binary stream of the uploaded PDF.

        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        try:
            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                return self._extract_text_from_pdfdoc(doc)
        except Exception as ex:
            logger.error(
                "Unexpected error during PyMuPDF parsing: %s",
                str(ex)
            )
            return []

    def extract_text_stream(self, stream: io.BytesIO) -> List[DocPageExtraction]:
        """Parses raw PDF stream for high-memory efficiency."""
        try:
            # pymupdf.open supports a file-like object via the 'stream' parameter
            with pymupdf.open(stream=stream, filetype="pdf") as doc:
                return self._extract_text_from_pdfdoc(doc)
        except Exception as ex:
            logger.error(
                "Unexpected error during stream parsing with PyMuPDF: %s",
                str(ex)
            )
            return []

    def _extract_text_from_pdfdoc(self, doc: pymupdf.Document) -> List[DocPageExtraction]:
        """Extract text from the PDF Doc."""
        extracted_pages: List[DocPageExtraction] = []
        try:
            for i in range(len(doc)):
                page = doc.load_page(i)
                text = page.get_text("text")
                extracted_pages.append(
                    DocPageExtraction(
                        page_number=i + 1,
                        text=text.strip()
                    )
                )
        except Exception as ex:
            logger.error(
                "Unexpected error during PyMuPDF parsing: %s",
                str(ex)
            )
        return extracted_pages
