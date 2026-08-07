from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.chunk import ParentChunk

class BaseChunker(ABC):
    """Interface for chunking strategies."""

    @abstractmethod
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[ParentChunk]:
        """Split raw text into structured Parent and Child chunks."""
        return
