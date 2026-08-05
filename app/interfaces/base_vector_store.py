from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """Abstract interface for Vector Databases."""

    @abstractmethod
    async def create_collection(
        self, collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Ensure/create vector collection with indexing parameters."""
        return

    @abstractmethod
    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """Upsert embedded points with structured metadata payloads."""
        return

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        return
