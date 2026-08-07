import uuid
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ChildChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str
    text: str
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParentChunk(BaseModel):
    parent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    token_count: int
    children: List[ChildChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
