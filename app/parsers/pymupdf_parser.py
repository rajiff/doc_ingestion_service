from typing import List, Dict, Any

import pymupdf

from app.interfaces import BasePDFParser

class PyMuPDFParser(BasePDFParser):
    """Concrete implementation of BasePDFParser using PyMuPdf.

    This parser uses PyMuPDF (fitz) library to extract text from PDF documents
    efficiently. It processes the entire document and returns page-level text
    chunks in a standardized format.
    """

    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses raw PDF bytes and extracts text chunked by page.

        Args:
            file_bytes: Raw binary stream of the uploaded PDF.

        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")

        pages: List[Dict[str, Any]] = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text("text")
            pages.append({"page_number": i + 1, "text": text})

        doc.close()
        return pages
