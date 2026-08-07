from typing import List, Dict, Any, Optional
import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from app.interfaces.base_vector_store import BaseVectorStore

class QdrantVectorStore(BaseVectorStore):
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = AsyncQdrantClient(host=host, port=port)

    async def create_collection(
        self, collection_name: str, vector_size: int, distance: str = "Cosine"
    ) -> bool:
        dist_enum = Distance.COSINE if distance.lower() == "cosine" else Distance.EUCLID
        collections = await self.client.get_collections()
        existing = [c.name for c in collections.collections]

        if collection_name not in existing:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=dist_enum)
            )
        return True

    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        point_ids = ids or [str(uuid.uuid4()) for _ in vectors]
        points = [
            PointStruct(id=p_id, vector=vec, payload=payload)
            for p_id, vec, payload in zip(point_ids, vectors, payloads)
        ]

        await self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        return True

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        hits = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k
        )

        return [{
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload}
            for hit in hits.points]

    async def delete_vectors_by_filter(
            self,
            collection_name: str,
            filter_key: str,
            filter_value: Any
        ) -> bool:
        await self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key=filter_key,
                        match=MatchValue(value=filter_value)
                    )
                ]
            )
        )
        return True
