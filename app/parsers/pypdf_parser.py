# app/parsers/pypdf_parser.py
import io
from typing import List

from pypdf import PdfReader, errors as pdf_reader_errors
from app.interfaces import BasePDFParser
from app.schemas.doc_ingestion import DocPageExtraction
from app.core.logger import logger

class PyPDFParser(BasePDFParser):
    """Concrete implementation of BasePDFParser using the 'pypdf' library."""

    def extract_text(self, file_bytes: bytes) -> List[DocPageExtraction]:
        """Parses raw PDF bytes, extracts raw text page-by-page
        from the provided PDF bytes."""
        try:
            # Wrap the bytes in a BytesIO stream
            bytes_stream = io.BytesIO(file_bytes)

            # Pass the stream to PdfReader
            pdf_reader = PdfReader(bytes_stream)

            extracted_pages = self._extract_text_from_pdf(pdf_reader)

            pdf_reader.close()

            return extracted_pages
        except pdf_reader_errors.PdfReadError as ex:
            logger.error("Error reading PDF: %s", str(ex))
            return []
        except Exception as ex:
            logger.exception("Unexpected error during parsing: %s", str(ex))

        return []

    def extract_text_stream(self, stream: io.BytesIO) -> List[DocPageExtraction]:
        """Parses raw PDF stream for high-memory efficiency."""
        try:
            # PdfReader accepts a file-like object (io.BytesIO) directly
            pdf_reader = PdfReader(stream)

            extracted_pages = self._extract_text_from_pdf(pdf_reader)

            pdf_reader.close()

            return extracted_pages
        except pdf_reader_errors.PdfReadError as ex:
            logger.error("Error reading PDF stream: %s", str(ex))
            return []
        except Exception as ex:
            logger.exception("Unexpected error during stream parsing: %s", str(ex))

        return []

    def _extract_text_from_pdf(self, pdf_reader: PdfReader) -> List[DocPageExtraction]:
        """Extract text from the page layer."""
        extracted_pages: List[DocPageExtraction] = []

        for page_idx, page in enumerate(pdf_reader.pages):
            try:
                # Extract text from the page layer
                raw_text = page.extract_text()

                # Fallback for empty pages or unextractable text matrices
                cleaned_text = raw_text.strip() if raw_text else ""

                if cleaned_text:
                    extracted_pages.append({
                        "page_number": page_idx + 1,
                        "text": cleaned_text
                    })
            except Exception as ex:
                logger.error(
                    "Error extracting text from page %s: %s",
                    page_idx + 1, str(ex))

        return extracted_pages
