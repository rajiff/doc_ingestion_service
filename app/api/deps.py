# Dependency injection (e.g., getting parser instances)
from app.core import settings, ParserType
from app.interfaces import BasePDFParser
from app.parsers import (
    PyPDFParser,
    PDFPlumberParser,
    PyMuPDFParser,
)

def get_parser(parser_type: ParserType | None = None) -> BasePDFParser:
    """
    Factory dependency resolving the strategy dynamically at runtime.
    """
    selected_type = parser_type or settings.DEFAULT_PARSER

    if selected_type == ParserType.PYPDF:
        return PyPDFParser()
    elif selected_type == ParserType.PDFPLUMBER:
        return PDFPlumberParser()
    elif selected_type == ParserType.PYMUPDF:
        return PyMuPDFParser()

    raise ValueError(f"Unsupported parser engine: {selected_type}")
