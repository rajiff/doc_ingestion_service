# app/services/pdf_ingestion_service.py
import hashlib
import uuid
from typing import BinaryIO
from app.interfaces import BasePDFParser
from app.interfaces.base_chunker import BaseChunker
from app.interfaces.base_embedder import BaseEmbeddingService
from app.interfaces.base_vector_store import BaseVectorStore
from app.schemas.doc_ingestion import DocIngestionResponse, DocChunkPayload


class PDFIngestionService:
    """
    Orchestrates the Document Ingestion Pipeline:
    1. Idempotency Check (via SHA-256 file checksums)
    2. PDF Parsing & Text Extraction
    3. Parent-Child Chunking Strategy
    4. Child Chunk Vector Embedding Generation
    5. Storage in Vector Database (Qdrant)
    """

    def __init__(
        self,
        parser: BasePDFParser,
        chunker: BaseChunker,
        embedder: BaseEmbeddingService,
        vector_store: BaseVectorStore,
        collection_name: str
    ):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.collection_name = collection_name

    def _calculate_checksum_stream(self, file_stream: BinaryIO) -> str:
        """
        RATIONALE: Memory-efficient hashing.
        Processes the stream in 64KB blocks rather than loading multi-megabyte
        files completely into memory at once.
        """
        sha256 = hashlib.sha256()
        while chunk := file_stream.read(65536):
            sha256.update(chunk)

        # Reset stream position for downstream text parsers
        file_stream.seek(0)
        return sha256.hexdigest()

    async def ingest_document(
        self,
        file_stream: BinaryIO,
        client_doc_id: str,
        force_reingest: bool = False
    ) -> DocIngestionResponse:
        """
        Main execution flow for ingesting and indexing a PDF document.
        """
        # Step 1: Compute binary checksum for idempotency checking
        checksum = self._calculate_checksum_stream(file_stream)

        # Step 2: Idempotency Check
        # Avoid expensive parsing and embedding calls if document is unchanged
        existing_doc = await self.vector_store.find_by_client_doc_id(
            collection_name=self.collection_name,
            client_doc_id=client_doc_id
        )

        if existing_doc and not force_reingest:
            if existing_doc.get("checksum") == checksum:
                return DocIngestionResponse(
                    client_doc_id=client_doc_id,
                    status="skipped",
                    checksum=checksum,
                    parent_chunks_indexed=existing_doc.get("parent_count", 0),
                    child_chunks_indexed=existing_doc.get("child_count", 0),
                    message="Document checksum matches existing record. Skipping ingestion."
                )

        try:
            # Step 3: Evict outdated vectors if re-ingesting modified document
            if existing_doc:
                await self.vector_store.delete_by_client_doc_id(
                    collection_name=self.collection_name,
                    client_doc_id=client_doc_id
                )

            # Step 4: Parse Document Text Page by Page
            extracted_pages = self.parser.extract_text(file_stream)

            # Step 5: Perform Parent-Child Chunking (Small-to-Big retrieval pattern)
            parent_chunks, child_chunks = self.chunker.split_pages(extracted_pages)

            # Step 6: Generate Embeddings (CHILD CHUNKS ONLY)
            # RATIONALE: We embed granular child text for vector similarity matching,
            # while mapping them back to parent chunk text in metadata for LLM synthesis.
            child_texts = [c.text for c in child_chunks]
            child_vectors = await self.embedder.embed_documents(child_texts)

            # Step 7: Construct Point Payloads for Vector Store
            points = []

            # Index Child Chunks with Vector Embeddings
            for idx, (chunk, vector) in enumerate(zip(child_chunks, child_vectors)):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{client_doc_id}_child_{idx}"))
                payload = DocChunkPayload(
                    chunk_id=point_id,
                    client_doc_id=client_doc_id,
                    parent_id=chunk.parent_id,
                    chunk_type="child",
                    text=chunk.text,
                    page_number=chunk.page_number,
                    checksum=checksum
                ).model_dump()

                points.append({"id": point_id, "vector": vector, "payload": payload})

            # Store Parent Chunks as Contextual Lookup Points
            for idx, p_chunk in enumerate(parent_chunks):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{client_doc_id}_parent_{idx}"))
                payload = DocChunkPayload(
                    chunk_id=point_id,
                    client_doc_id=client_doc_id,
                    parent_id=None,
                    chunk_type="parent",
                    text=p_chunk.text,
                    page_number=p_chunk.page_number,
                    checksum=checksum
                ).model_dump()

                points.append({"id": point_id, "vector": [], "payload": payload})

            # Step 8: Upsert points into Qdrant
            await self.vector_store.upsert_points(
                collection_name=self.collection_name,
                points=points
            )

            return DocIngestionResponse(
                client_doc_id=client_doc_id,
                status="success",
                checksum=checksum,
                parent_chunks_indexed=len(parent_chunks),
                child_chunks_indexed=len(child_chunks),
                message="Document successfully processed and indexed."
            )

        except Exception as e:
            return DocIngestionResponse(
                client_doc_id=client_doc_id,
                status="failed",
                checksum=checksum,
                message="Error encountered during ingestion execution.",
                error_details=str(e)
            )
