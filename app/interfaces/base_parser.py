from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BasePDFParser(ABC):
    """
    Abstract Base Class Document parsing
    
    Enforcing the interface for all text extraction strategies.
    Ensures conformance to the Open-Closed Principle.
    """

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parses raw PDF bytes and extracts text chunked by page.

        Args:
            file_bytes: Raw binary stream of the uploaded PDF.

        Returns:
            A list of dictionaries, where each dict represents a page containing
            metadata (e.g., page number) and the raw extracted text string.
        """
        pass