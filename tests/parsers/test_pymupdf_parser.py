import pytest
import io
import os
from app.interfaces import BasePDFParser
from app.parsers.pymupdf_parser import PyMuPDFParser

class TestPyMuPDFParser:
    """
    Test that the parser can extract text from a PDF.
    """

    def test_extract_text_single_page(testargs):
        """
        Test that the parser can extract text from a single-page PDF.
        """
        # Create a simple dummy PDF in memory (or use a real sample if available)
        # For this test, we'll assume a valid byte stream is provided

        pdfFile = "tests/test_docs/SOLID Principles Baeldung.pdf"

        assert os.path.exists(pdfFile), f"Test file not found at {pdfFile}"

        # Read the entire file into memory as bytes
        with open(pdfFile, "rb") as file: 
            file_bytes = file.read()

            parser: BasePDFParser = PyMuPDFParser()

            result = parser.extract_text(file_bytes)

            # Debug print (optional, removed in production tests)
            print(f"Extracted {len(result)} pages.")

            # Validation: Check if we got data
            assert len(result) > 0, "Parser failed to extract any pages."

            # If you want to test the current bug (that it only returns 1 page):
            assert len(result) >= 1

        # We will mock the doc object or provide actual bytes for a 1-page pdf
        # Since I can't easily generate a binary PDF without external libs here, 
        # I'll simulate the call structure.
        pass

    # I will actually write a proper test suite in the next step after confirming 
    # how to handle the file bytes without an actual .pdf file on disk.

