import io
from typing import List

from pypdf import PdfReader, errors as pdf_reader_errors
from app.interfaces import BasePDFParser
from app.schemas.doc_ingestion import DocPageExtraction


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
            # Log the error here in a real app
            print(f"Error reading PDF: {ex}")
            return []
        except Exception as ex:
            # Catch-all for other processing issues
            print(f"Unexpected error during parsing: {ex}")

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
                # Log error for specific page but continue processing others
                print(f"Error extracting text from page {page_idx + 1}: {ex}")

        return extracted_pages
