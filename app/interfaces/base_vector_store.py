from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """Abstract interface for Vector Databases."""

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Ensure/create vector collection with indexing parameters.
        Arguments:
            collection_name -- name of the collection to create.
            vector_size -- size of each vector.
            distance -- metric to use for similarity.
        Returns:
           bool indicating success/failure.
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
        """Upsert embedded points with structured metadata payloads.
        Arguments:
           collection_name -- name of the collection to upert vectors.
           vectors -- list of vectors to upsert.
           payloads -- list of metadata payloads.
           ids -- optional list of ids for the vectors.
        Returns:
           bool indicating success/failur
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
        """Perform vector similarity search.
        Arguments:
            collection_name -- name of the collection
            query_vector -- query vector to search against.
            top_k -- number of top results to return.
            filters -- optional filters to apply during search.
        Returns:
           list of dictionaries containing ids,
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
            collection_name -- name of the collection in which points will be deleted.
            filter_key -- key in the metadata to match points with.
            filter_value -- value to match points with.
        Returns:
            bool indicating whether any points were deleted.
        """
        return
