# app/schemas/retrieval.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocQueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="User search query string"
    )
    top_k: int = Field(
        default=5,
        ge=1, le=20,
        description="Number of top child chunks to retrieve"
    )
    client_doc_id: Optional[str] = Field(
        None,
        description="Optional metadata filter by document ID"
    )

class DocChunkChildHit(BaseModel):
    child_id: str
    parent_id: str
    score: float
    text: str
    metadata: Dict[str, Any]

class DocStitchedContext(BaseModel):
    parent_id: str
    parent_text: str
    child_hits: List[DocChunkChildHit]
    metadata: Dict[str, Any]

class DocQueryResponse(BaseModel):
    query: str
    contexts: List[DocStitchedContext]
    total_chunks_retrieved: int
