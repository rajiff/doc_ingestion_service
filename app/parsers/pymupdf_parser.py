from app.interfaces import BasePDFParser

import pymupdf
import fit
from typing import List, Dict, Any


# PyMuPDF concrete strategy

class PyMuPDFParser(BasePDFParser):
    """
    Concrete implementation of BasePDFParser using PyMuPdf
    """

    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parses raw PDF bytes and extracts text chunk
        """

        # doc = fit.open(file_bytes)
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")

        pages = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text("text")
            pages.append({"page_number": i + 1, "text": text})

        doc.close()
        
        # Return the list of pages with extracted text
        return pages


