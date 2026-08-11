from app.core.config import ParserType, settings
from app.interfaces import (
    BasePDFParser,
    BaseEmbeddingService,
    BaseVectorStore,
    BaseChunker
)
from app.parsers import (
    PyPDFParser,
    PDFPlumberParser,
    PyMuPDFParser,
)
from app.services import (
    OllamaEmbeddingService,
    QdrantVectorStore,
    ParentChildChunker,
    PDFIngestionService
)

def get_pdf_parser() -> BasePDFParser:
    """Factory to instantiate the configured parser strategy at runtime"""
    if settings.DEFAULT_PARSER == ParserType.PYPDF:
        return PyPDFParser()
    if settings.DEFAULT_PARSER == ParserType.PDFPLUMBER:
        return PDFPlumberParser()
    if settings.DEFAULT_PARSER == ParserType.PYMUPDF:
        return PyMuPDFParser()

    raise ValueError(f"Unsupported parser engine: {settings.DEFAULT_PARSER}")

def get_embedding_service() -> BaseEmbeddingService:
    """Factory to instantiate the configured embedding provider at runtime."""
    if settings.EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddingService(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBED_MODEL
        )
    raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")

def get_vector_store() -> BaseVectorStore:
    """Factory to instantiate the configured vector store at runtime."""
    if settings.VECTOR_STORE_PROVIDER == "qdrant":
        return QdrantVectorStore(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
    raise ValueError(
        f"Unsupported vector store provider: {settings.VECTOR_STORE_PROVIDER}")

def get_chunking_service() -> BaseChunker:
    """Instantiate configured chunking service."""
    return ParentChildChunker(
        parent_chunk_size=600,
        child_chunk_size=150
    )

def get_ingestion_service() -> PDFIngestionService:
    """Instantiate configured ingestion service."""
    parser = get_pdf_parser()
    chunker = get_chunking_service()
    embedder =get_embedding_service()
    vector_store = get_vector_store()

    return PDFIngestionService(
        parser=parser,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        collection_name=settings.QDRANT_COLLECTION_NAME
    )
