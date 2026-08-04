from typing import List
from pydantic import BaseModel, Field

class DocPageExtraction(BaseModel):
    """Schemas individual page contents."""
    page_number: int = Field(..., description="page number index.")
    text: str = Field(..., description="Text extracted, cleaned from the page.")

class DocIngestionMetadata(BaseModel):
    """Metadata surrounding the extraction run."""
    filename: str = Field(..., description="The name of the processed file.")
    parser_used: str = Field(..., description="Parsing strategy utilized (etc., pypdf, pdfplumber)")
    total_pages: int = Field(..., description="Total pages successfully parsed.")

class DocIngestionResponse(BaseModel):
    """The unified container returned by our microservice layer."""
    metadata: DocIngestionMetadata
    pages: List[DocPageExtraction]
