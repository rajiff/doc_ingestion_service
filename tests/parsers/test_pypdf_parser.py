import os
from app.interfaces import BasePDFParser
from app.parsers import PyPDFParser

class TestPyPDFParser:
    """
    Test that the parser can extract text from a PDF.
    """

    def test_extract_text_single_page(testargs):
        """
        Test that the parser can extract text from a single-page PDF.
        """

        pdfFile = "tests/test_docs/Critical Thinking 10 Year Kids.pdf"
        assert os.path.exists(pdfFile), f"Test file not found at {pdfFile}"

        # Read the entire file into memory as bytes
        with open(pdfFile, "rb") as file: 
            file_bytes = file.read()

            parser: BasePDFParser = PyPDFParser()
            result = parser.extract_text(file_bytes)

            # Debug print (optional, removed in production tests)
            print(f"Extracted {len(result)} pages from PyPDFParser.")

            # Validation: Check if we got data
            assert len(result) > 0, "Parser failed to extract any pages."

            # If you want to test the current bug (that it only returns 1 page):
            assert len(result) >= 1

        return
