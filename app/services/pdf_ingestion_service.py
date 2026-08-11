# app/services/pdf_ingestion_service.py
import hashlib
import uuid
from typing import BinaryIO, List
from app.interfaces import (
    BasePDFParser,
    BaseChunker,
    BaseEmbeddingService,
    BaseVectorStore
)
from app.schemas.doc_ingestion import (
    DocIngestionResponse,
    DocChunkPayload,
    DocPageExtraction
)
from app.core.exceptions import CollectionNotFoundError
from app.core.logger import logger

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
        # Step 1: Idempotency Check & Cold Start Guard
        # Avoid expensive parsing and embedding calls if document is unchanged
        existing_doc = None
        collection_needs_creation = False

        try:
            existing_doc_records = await self.vector_store.find_by_client_doc_id(
                collection_name=self.collection_name,
                client_doc_id=client_doc_id
            )
            if len(existing_doc_records) > 0:
                existing_doc = existing_doc_records[0]

            # @TODO if more than one is returned?
        except CollectionNotFoundError as ex:
            existing_doc = None
            collection_needs_creation = True
            logger.info("Collection %s not exists, will create it, error %s",
                        self.collection_name,
                        str(ex))

        # Step 2: Compute binary checksum for idempotency checking
        checksum = self._calculate_checksum_stream(file_stream)

        if existing_doc and not force_reingest:
            if existing_doc.get("checksum") == checksum:
                return DocIngestionResponse(
                    client_doc_id=client_doc_id,
                    status="skipped",
                    checksum=checksum,
                    parent_chunks_indexed=existing_doc.get("parent_count", 0),
                    child_chunks_indexed=existing_doc.get("child_count", 0),
                    message="Document exists already. Skipping ingestion."
                )

        try:
            # Step 3: Evict outdated vectors if re-ingesting modified document
            if existing_doc:
                await self.vector_store.delete_by_client_doc_id(
                    collection_name=self.collection_name,
                    client_doc_id=client_doc_id
                )

            # Step 4: Parse Document Text Page by Page
            extracted_pages: List[DocPageExtraction] = []
            extracted_pages = self.parser.extract_text(file_stream.read())

            # Step 5: Perform Parent-Child Chunking (Small-to-Big retrieval pattern)
            # parent_chunks, child_chunks = self.chunker.chunk_text(extracted_pages)
            all_parent_chunks = []
            flat_child_chunks = []
            parent_text_map = {}

            for page in extracted_pages:
                # Skip empty pages to save processing time
                if not page.text.strip():
                    continue

                 # Pass clean page metadata
                parents = self.chunker.chunk_text(
                    text=page.text,
                    metadata={"page_number": page.page_number}
                )

                for parent in parents:
                    all_parent_chunks.append(parent)
                    parent_text_map[parent.parent_id] = parent.text
                    for child in parent.children:
                        flat_child_chunks.append(child)

            if not flat_child_chunks:
                return DocIngestionResponse(
                    client_doc_id=client_doc_id,
                    status="skipped",
                    checksum=checksum,
                    message="Document contains no indexable text."
                )

            # Step 6: Generate Embeddings (CHILD CHUNKS ONLY)
            # RATIONALE: We embed granular child text for vector similarity matching,
            # while mapping them back to parent chunk text
            # in metadata for LLM synthesis
            child_texts = [child.text for child in flat_child_chunks]
            child_vectors = await self.embedder.embed_documents(child_texts)

            # Step 7: Construct Point Payloads for Vector Store
            point_ids: List[str] = []
            vectors: List[List[float]] = []
            payloads: List[dict] = []

            for idx, (child, vector) in enumerate(zip(flat_child_chunks, child_vectors)):
                point_id = str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{client_doc_id}_child_{idx}"))
                page_num = child.metadata.get("page_number", 1)  # Fixed bitwise bug

                payload = DocChunkPayload(
                    chunk_id=point_id,
                    client_doc_id=client_doc_id,
                    parent_id=child.parent_id,
                    chunk_type="child",
                    text=child.text,
                    parent_text=parent_text_map.get(child.parent_id, ""),
                    page_number=page_num,
                    checksum=checksum
                ).model_dump()

                point_ids.append(point_id)
                vectors.append(vector)
                payloads.append(payload)

            # Conditional Lazy Initialization of Collection in Vector Database
            if collection_needs_creation:
                logger.info("Collection %s is not created. Creating now...",
                            self.collection_name)
                # Get thelength of the vector embeddings from any one of the chunks
                vector_size = len(child_vectors[0]) if child_vectors else 0

                await self.vector_store.create_collection(
                    collection_name=self.collection_name,
                    vector_size=vector_size
                )
                logger.info("Collection %s created successfully.", self.collection_name)

            # Step 8: Upsert points into Qdrant
            await self.vector_store.upsert_vectors(
                collection_name=self.collection_name,
                vectors=vectors,
                payloads=payloads,
                ids=point_ids
            )

            return DocIngestionResponse(
                client_doc_id=client_doc_id,
                status="success",
                checksum=checksum,
                parent_chunks_indexed=len(all_parent_chunks),
                child_chunks_indexed=len(flat_child_chunks),
                message="Document successfully processed and indexed."
            )

        except Exception as e:
            logger.error("An error occurred while ingesting the document, error: %s",
                         str(e))
            return DocIngestionResponse(
                client_doc_id=client_doc_id,
                status="failed",
                checksum=checksum,
                message="Error encountered during ingestion execution.",
                error_details=str(e)
            )
