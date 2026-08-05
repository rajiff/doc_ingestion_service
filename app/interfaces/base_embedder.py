from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingService(ABC):
    """Abstract interface for all embedding providers."""

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        return

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document chunks/texts in batch."""
        return

    @property
    @abstractmethod
    async def dimension(self) -> int:
        """Return the vector dimensionality of the model
        (e.g., 768 for nomic-embed-text)."""
        return
