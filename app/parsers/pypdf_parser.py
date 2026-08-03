import io
from typing import List, Dict, Any
from pypdf import PdfReader, errors as pdf_reader_errors
from app.interfaces import BasePDFParser

# PyPDF concrete strategy
class PyPDFParser(BasePDFParser):
    """
    Concrete implementation of BasePDFParser using the 'pypdf' library.
    Processes the PDF entirely in-memory using binary byte streams.
    """

    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parses raw PDF bytes, extracts raw text page-by-page from the provided PDF bytes.

        Args:
            file_bytes: Raw binary stream of the uploaded PDF.

        Returns:
            A list of dicts matching the required interface structure.
        """
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

    def _extract_text_from_pdf(self, pdfReader: PdfReader) -> List[Dict[str, Any]]:
        extracted_pages: List[Dict[str, Any]] = []

        for page_idx, page in enumerate(pdfReader.pages):
            try:
                # Extract text from the page layer
                raw_text = page.extract_text()

                # Fallback for empty pages or unextractable text matrices
                cleaned_text = raw_text.strip() if raw_text else ""

                if cleaned_text:
                    extracted_pages.append({
                        "page_number": page_idx + 1,  # Standardize to 1-indexed count
                        "text": cleaned_text
                    })
            except Exception as ex:
                # Log error for specific page but continue processing others
                print(f"Error extracting text from page {page_idx + 1}: {ex}")

        return extracted_pages


