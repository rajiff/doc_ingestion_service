from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingService(ABC):
    """Abstract interface for all embedding providers."""

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query string.
        Arguments:
           text -- The string to embed.
        """
        return

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document chunks/texts in batch.
        Arguments:
           texts -- A list of strings to be embedded.
        """
        return

    @abstractmethod
    async def get_dimension(self) -> int:
        """Return the vector dimensionality of the model"""
        return
