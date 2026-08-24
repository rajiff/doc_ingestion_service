# app/services/pdf_retrieval_service.py
from typing import List, Dict
from app.interfaces.base_vector_store import BaseVectorStore
from app.interfaces import BaseEmbeddingService
from app.schemas.doc_retrieval import (
    DocQueryRequest,
    DocQueryResponse,
    DocChunkChildHit,
    DocStitchedContext
)
from app.core.logger import logger
from app.core.config import settings
from app.core.observability import (
    business_operation,
    BusinessCapability,
    capture_arguments
)

class PDFRetrievalService:
    """
    Orchestrates the read-path for Parent-Child context retrieval.
    1. Embeds user query string.
    2. Searches for nearest child chunks in Qdrant.
    3. Fetches parent chunks by ID to reconstruct full narrative context.
    """
    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: BaseEmbeddingService,
        collection_name: str = settings.PDF_INGESTION_VECTOR_NAME
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.collection_name = collection_name

    @business_operation(
        label="retrieve_context",
        capability=BusinessCapability.DOCUMENT_QUERY,
        attribute_provider=capture_arguments(
            request="document.query.request"
        )
    )
    async def retrieve_context(
            self,
            request: DocQueryRequest
        ) -> DocQueryResponse:
        """Executes the retrieval process for Parent-Child context"""
        # Pre-execution Validation
        cleaned_query = request.query.strip()
        if not cleaned_query:
            raise ValueError("Query string cannot be empty or blank.")

        logger.info(
            "Executing vector search for query: '%s' (top_k=%d, client_doc_id=%s)",
            cleaned_query,
            request.top_k,
            request.client_doc_id
        )

        try:
            # Step 1: Embed query text using the abstract embedding interface
            query_vector = await self.embedder.embed_query(cleaned_query)

            # Step 2: Build metadata filters if client_doc_id is scoped
            filters = {}
            if request.client_doc_id:
                filters["client_doc_id"] = request.client_doc_id

            # Step 3: Vector search against child chunks using existing search() signature
            raw_hits = await self.vector_store.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                top_k=request.top_k,
                filters=filters if filters else None,
                score_threshold=settings.RAG_COSINE_SCORE_THRESHOLD
            )

            if not raw_hits:
                logger.info("No matching child chunks found for query.")
                return DocQueryResponse(
                    query=cleaned_query,
                    contexts=[],
                    total_chunks_retrieved=0
                )

            logger.debug(
                "Found %d matching doc search results",
                len(raw_hits)
            )

            # Step 4: Group child hits by parent_id for parent context lookup
            # This in code or in memory grouping makes this vector database agnostic
            parent_to_children: Dict[str, List[DocChunkChildHit]] = {}

            for hit in raw_hits:
                payload = hit.get("payload", {})

                # Only operate on child chunks
                if payload.get("chunk_type") != "child":
                    continue

                parent_id = payload.get("parent_id")
                if not parent_id:
                    continue

                child_hit = DocChunkChildHit(
                    child_id=hit["id"],
                    parent_id=parent_id,
                    score=hit.get("score", 0.0),
                    text=payload.get("text", ""),
                    metadata={
                        "page_number": payload.get("page_number"),
                        "client_doc_id": payload.get("client_doc_id"),
                        "checksum": payload.get("checksum")
                    }
                )

                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                parent_to_children[parent_id].append(child_hit)

            # If no valid child hits were parsed
            if not parent_to_children:
                logger.info("Failed to find any valid child hits.")
                return DocQueryResponse(
                    query=cleaned_query,
                    contexts=[],
                    total_chunks_retrieved=0
                )

            # Step 5: Batch fetch parent payloads using direct point primary key lookup
            parent_ids = list(parent_to_children.keys())
            parent_records = await self.vector_store.get_by_ids(
                collection_name=self.collection_name,
                ids=parent_ids
            )

            # Step 6: Stitch parent chunks with their child hits
            stitched_contexts: List[DocStitchedContext] = []
            for record in parent_records:
                p_id = record["id"]
                p_payload = record.get("payload", {})

                stitched_contexts.append(
                    DocStitchedContext(
                        parent_id=p_id,
                        parent_text=p_payload.get("text", ""),
                        child_hits=parent_to_children.get(p_id, []),
                        metadata={
                            "page_number": p_payload.get("page_number"),
                            "client_doc_id": p_payload.get("client_doc_id")
                        }
                    )
                )

            return DocQueryResponse(
                query=cleaned_query,
                contexts=stitched_contexts,
                total_chunks_retrieved=len(raw_hits)
            )

        except Exception as ex:
            logger.error("Failed to process retrieval query: %s", str(ex), exc_info=True)
            raise RuntimeError(f"Retrieval operation failed: {str(ex)}") from ex
