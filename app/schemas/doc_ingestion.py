from typing import Optional
from pydantic import BaseModel, Field

# --- Internal DTOs (Parser -> Service) ---

class DocPageExtraction(BaseModel):
    """Schemas for internal page extraction results"""
    page_number: int = Field(..., description="page number index(1 - n).")
    text: str = Field(..., description="Extracted and Cleaned page text")

class DocChunkPayload(BaseModel):
    """Schema for internal chunking pipeline execution."""
    # PS: ... => mandatory
    chunk_id: str = Field(
        ..., description="Deterministic UUID point ID")
    client_doc_id: str = Field(
        ..., description="External client document identifier")
    parent_id: Optional[str] = Field(
        None, description="Parent chunk UUID if child chunk")
    chunk_type: str = Field(
        ..., description="'parent' or 'child'")
    text: str = Field(
        ..., description="Text content")
    page_number: int = Field(
        ..., description="Page where chunk originated")
    checksum: str = Field(
        ..., description="SHA-256 binary hash of the original document")

# --- External API Request/Response Schemas (API Boundary) ---

class DocIngestionRequest(BaseModel):
    """Parameters passed alongside the uploaded file in FastAPI Form/Query."""
    client_doc_id: str = Field(
        ..., description="Mandatory unique client document identifier (e.g., LMS_101)")

    force_reingest: bool = Field(
        default=False, description="If True, overwrites existing document vectors")

class DocIngestionResponse(BaseModel):
    """Standard API response for the ingestion pipeline."""
    client_doc_id: str = Field(
        ..., description="External client identifier")
    status: str = Field(
        ..., description="Execution outcome: 'success', 'skipped', or 'failed'")
    checksum: str = Field(
        ..., description="SHA-256 hash of ingested file")
    parent_chunks_indexed: int = Field(
        default=0, description="Total parent chunks stored")
    child_chunks_indexed: int = Field(
        default=0, description="Total child chunks indexed")
    message: str = Field(
        ..., description="Human-readable result summary")
    error_details: Optional[str] = Field(
        None, description="Detailed error trace if status is 'failed'")
