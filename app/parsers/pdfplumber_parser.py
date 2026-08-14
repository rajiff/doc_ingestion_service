import io
from typing import List

import pdfplumber
from app.interfaces import BasePDFParser
from app.schemas.doc_ingestion import DocPageExtraction
from app.core.logger import logger

class PDFPlumberParser(BasePDFParser):
    """Concrete implementation of BasePDFParser using the 'pdfplumber' library."""

    def extract_text(self, file_bytes: bytes) -> List[DocPageExtraction]:
        """Parses raw PDF bytes and extracts text chunked by page.
        Args:
            file_bytes: Raw binary stream of the uploaded PDF.
        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return self._extract_text_from_pdf(pdf)
        except Exception as ex:
            logger.error("Unexpected error during PDFPlumber parsing: %s", str(ex))
            return []

    def extract_text_stream(self, stream: io.BytesIO) -> List[DocPageExtraction]:
        """Parses raw PDF stream for high-memory efficiency."""
        try:
            with pdfplumber.open(stream) as pdf:
                return self._extract_text_from_pdf(pdf)
        except Exception as ex:
            logger.error(
                "Unexpected error during stream parsing with PDFPlumber: %s",
                str(ex)
            )
            return []

    def _extract_text_from_pdf(self, pdf) -> List[DocPageExtraction]:
        """Extract text from the page layer."""
        extracted_pages: List[DocPageExtraction] = []
        for i, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text()
                if text and text.strip():
                    extracted_pages.append(
                        DocPageExtraction(
                            page_number=i,
                            text=text.strip()
                        )
                    )
            except Exception as ex:
                logger.error(
                    "Error extracting text from page %s: %s",
                    i, str(ex)
                )
        return extracted_pages
