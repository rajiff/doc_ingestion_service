from app.core.config import settings
from app.interfaces import (
    BaseEmbeddingService,
    BaseVectorStore,
    BaseChunker
)

from app.services import (
    OllamaEmbeddingService,
    QdrantVectorStore,
    ParentChildChunker
)

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
