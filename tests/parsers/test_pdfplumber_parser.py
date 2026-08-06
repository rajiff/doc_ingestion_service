import os
from app.interfaces import BasePDFParser
from app.parsers import PDFPlumberParser

class TestPDFPlumberParser:
    """
    Test that the parser can extract text from a PDF.
    """

    def test_extract_text_single_page(self, _):
        """
        Test that the parser can extract text from a PDF file.
        """

        pdf_doc_file = "tests/test_docs/Physics for 10 year Kids.pdf"
        assert os.path.exists(pdf_doc_file), f"Test file not found at {pdf_doc_file}"

        # Read the entire file into memory as bytes
        with open(pdf_doc_file, "rb") as file:
            file_bytes = file.read()

            parser: BasePDFParser = PDFPlumberParser()
            result = parser.extract_text(file_bytes)

            # Debug print (optional, removed in production tests)
            print(f"Extracted {len(result)} pages from PDFPlumberParser.")

            # Validation: Check if we got data
            assert len(result) > 0, "PDFPlumber Parser failed to extract any pages."
            assert len(result) >= 1

        return
