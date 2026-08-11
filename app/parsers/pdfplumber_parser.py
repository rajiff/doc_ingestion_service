import io
from typing import List

import pdfplumber

from app.interfaces import BasePDFParser
from app.schemas.doc_ingestion import DocPageExtraction

class PDFPlumberParser(BasePDFParser):
    """Concrete implementation of BasePDFParser using PDFPlumber.
    Parser implementation using PDFPlumber library for text extraction from PDF files.
    This parser uses PDFPlumber library to extract text from PDF documents
    with high-quality text extraction capabilities including tables and complex layouts.
    """

    def extract_text(self, file_bytes: bytes) -> List[DocPageExtraction]:
        """Parses raw PDF bytes and extracts text chunked by page.
        Args:
            file_bytes: Raw binary stream of the uploaded PDF.
        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """

        pages: List[DocPageExtraction] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                pages.append(DocPageExtraction(page_number=i, text=text))
        return pages
