from abc import ABC, abstractmethod
from typing import BinaryIO, List
from app.schemas.doc_ingestion import DocPageExtraction

class BasePDFParser(ABC):
    """Abstract Base Class Document parsing.

    Enforcing the interface for all text extraction strategies.
    Ensures conformance to the Open-Closed Principle.
    """

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> List[DocPageExtraction]:
        """Parses raw PDF bytes and extracts text chunked by page.

        Args:
            file_bytes: Raw binary bytes of the uploaded PDF.

        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        return

    @abstractmethod
    def extract_text_stream(self, stream: BinaryIO) -> List[DocPageExtraction]:
        """Parses raw PDF stream for high-memory efficiency.

        Args:
            stream: A binary stream of the uploaded PDF (e.g., BytesIO or File).

        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        return
