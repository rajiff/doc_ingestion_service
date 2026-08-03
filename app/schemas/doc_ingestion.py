from pydantic import BaseModel, Field
from typing import List, Optional

# Schema for (ExtractionRequest/Response/Metadata)

class DocPageExtraction(BaseModel):
    """
    Schemas individual page contents 
    """
    page_number: int = Field(..., description="The 1-indexed page number of the document.")
    text: str = Field(..., description="The raw or stripped text content extracted from this page.")

class DocIngestionMetadata(BaseModel):
    """Metadata surrounding the extraction run."""
    filename: str = Field(..., description="The name of the processed file.")
    parser_used: str = Field(..., description="The engine strategy utilized (e.g., pypdf, pdfplumber).")
    total_pages: int = Field(..., description="Total pages successfully parsed.")

class DocIngestionResponse(BaseModel):
    """The unified container returned by our microservice layer."""
    metadata: DocIngestionMetadata
    pages: List[DocPageExtraction]