from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """Abstract Base Class for Vector Store Operations."""

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Ensure/create vector collection with indexing parameters.
        Args:
            collection_name: Name of the target collection.
            vector_size: Dimension size of vector embeddings.
            distance: Similarity metric to use (Cosine, Dot, Euclidean).

        Returns:
            bool: True if collection is ready.
        """
        return

    @abstractmethod
    async def find_by_client_doc_id(
        self,
        collection_name: str,
        client_doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves points/records matching a specific client_doc_id from metadata payload.
        Used for checking document idempotency prior to ingestion.

        Args:
            collection_name: Name of the collection to search in.
            client_doc_id: Unique client document identifier.

        Returns:
            List[Dict[str, Any]]: List of dictionary metadata payloads
            for matching chunks.
        """
        return

    @abstractmethod
    async def delete_by_client_doc_id(
        self,
        collection_name: str,
        client_doc_id: str
    ) -> None:
        """
        Deletes all chunks/points associated with a specific client_doc_id.
        Used primarily during force re-ingestion to wipe out stale vectors.

        Args:
            collection_name: Target collection name.
            client_doc_id: Unique client document identifier.

        Returns:
            bool: True if deletion operation succeeded.
        """
        return

    @abstractmethod
    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Upserts parent/child vector embeddings alongside their
        structured metadata payloads.

        Args:
            collection_name: Name of the collection.
            vectors: List of embedding vector arrays.
            payloads: List of metadata dictionaries corresponding to vectors.
            ids: Optional list of explicit point IDs.

        Returns:
            bool: True if upsert succeeded.
        """
        return

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against indexed records.

        Args:
            collection_name: Target collection name.
            query_vector: Query dense embedding vector.
            top_k: Top K nearest neighbor results to retrieve.
            filters: Optional metadata filtering conditions.

        Returns:
            List[Dict[str, Any]]: Ranked list of matching payloads
            and score metrics.
        """
        return

    @abstractmethod
    async def delete_vectors_by_filter(
        self,
        collection_name: str,
        filter_key: str,
        filter_value: Any
    ) -> bool:
        """Delete all points matching a specific payload metadata criterion.
        Arguments:
            collection_name: name of the collection in which points will be deleted.
            filter_key: key in the metadata to match points with.
            filter_value: value to match points with.
        Returns:
            bool indicating whether any points were deleted.
        """
        return
