import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from app.core.logger import logger
from app.interfaces.base_vector_store import BaseVectorStore

class QdrantVectorStore(BaseVectorStore):
    """
    Concrete implementation of BaseVectorStore using Qdrant.
    Handles collection setup, indexed document lookup, atomic filtered deletions,
    and vector similarity search.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = AsyncQdrantClient(host=host, port=port)

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """
        Ensures target collection exists and initializes payload keyword indexes
        (e.g. client_doc_id) for O(1) idempotency lookups.
        """
        try:
            # Map distance metric string to Qdrant Distance enum
            distance_map = {
                "Cosine": qdrant_models.Distance.COSINE,
                "Dot": qdrant_models.Distance.DOT,
                "Euclidean": qdrant_models.Distance.EUCLID,
            }
            qdrant_distance = distance_map.get(distance, qdrant_models.Distance.COSINE)

            # Check if collection already exists
            collections_response = await self.client.get_collections()
            existing_names = [col.name for col in collections_response.collections]

            if collection_name not in existing_names:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=vector_size,
                        distance=qdrant_distance,
                    ),
                )
                logger.info("Created Qdrant collection '%s'.", collection_name)

            # Crucial Optimization: Create Keyword Index on client_doc_id payload field
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="client_doc_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            logger.info("Payload index for 'client_doc_id' ensured in '{%s}'.",
                        collection_name)
            return True

        except Exception as e:
            logger.error("Failed to initialize collection '{%s}': {%s}",
                         collection_name, str(e))
            raise e

    async def find_by_client_doc_id(
        self,
        collection_name: str,
        client_doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Queries Qdrant points matching payload client_doc_id.
        Disables vector retrieval (with_vectors=False) to optimize network bandwidth.
        """
        try:
            match_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="client_doc_id",
                        match=qdrant_models.MatchValue(value=client_doc_id),
                    )
                ]
            )

            # Scroll through matching points without loading float vectors
            scroll_result, _ = await self.client.scroll(
                collection_name=collection_name,
                scroll_filter=match_filter,
                limit=250,  # Max payload items returned per lookup batch
                with_payload=True,
                with_vectors=False,  # RAM/IO Optimization: exclude dense embeddings
            )

            return [point.payload for point in scroll_result if point.payload]

        except Exception as e:
            logger.error(
                "Error retrieving payloads for client_doc_id '%s': ': %s",
                client_doc_id, str(e)
            )
            raise e

    async def delete_by_client_doc_id(
        self,
        collection_name: str,
        client_doc_id: str
    ) -> bool:
        """
        Deletes all vector points associated with client_doc_id
        using Qdrant's Filtered Delete.
        """
        try:
            delete_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="client_doc_id",
                        match=qdrant_models.MatchValue(value=client_doc_id),
                    )
                ]
            )

            await self.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.FilterSelector(filter=delete_filter),
            )

            logger.info("Deleted existing records for client_doc_id '%s'.", client_doc_id)
            return True

        except Exception as e:
            logger.error(
                "Failed to delete records for client_doc_id '%s': %s",
                client_doc_id, str(e)
            )
            raise e

    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Batch upserts vector points with structured metadata payloads into Qdrant.
        """
        try:
            # Generate UUID string IDs if none are provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            points = [
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=payload
                )
                for point_id, vec, payload in zip(ids, vectors, payloads)
            ]

            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            return True

        except Exception as e:
            logger.error("Failed to upsert vectors into '%s': %s",
                         collection_name, str(e))
            raise e

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes dense vector similarity search with optional filter conditions.
        """
        try:
            qdrant_filter = None
            if filters:
                # Convert basic filter dict key-values into Qdrant FieldConditions
                must_conditions = [
                    qdrant_models.FieldCondition(
                        key=k,
                        match=qdrant_models.MatchValue(value=v)
                    )
                    for k, v in filters.items()
                ]
                qdrant_filter = qdrant_models.Filter(must=must_conditions)

            search_result = await self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True
            )

            # Map point hits to response dictionaries including payload and score
            results = []
            for hit in search_result.points:
                item = hit.payload or {}
                item["_id"] = hit.id
                item["_score"] = hit.score
                results.append(item)

            return results

        except Exception as e:
            logger.error("Error performing vector search in '%s': %s",
                         collection_name, str(e))
            raise e

    async def delete_vectors_by_filter(
        self,
        collection_name: str,
        filter_key: str,
        filter_value: Any
    ) -> bool:
        await self.client.delete(
            collection_name=collection_name,
            points_selector=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key=filter_key,
                        match=qdrant_models.MatchValue(value=filter_value)
                    )
                ]
            )
        )
        return True
