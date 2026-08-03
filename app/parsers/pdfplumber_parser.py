from app.interfaces import BasePDFParser

import pdfplumber
import io
from typing import List, Dict, Any

# PDFPlumber concrete strategy

class PDFPlumberParser(BasePDFParser):
    """
    Concrete implementation of BasePDFParser using PDFPlumber
    """

    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parses raw PDF bytes and extracts text chunk
        """

        pages = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                i += 1
                text = page.extract_text()
                if not text:
                    continue
                pages.append({"page_number": i, "text": text})

        return pages
