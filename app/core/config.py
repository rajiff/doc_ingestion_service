from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class ParserType(str, Enum):
    PYPDF = "pypdf"
    PDFPLUMBER = "pdfplumber"
    PYMUPDF = "pymupdf"  # PyMuPDF

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF Ingestion Service"
    PROJECT_DESC: str = "Service for extracting text from PDF documents"
    DEFAULT_PARSER: ParserType = ParserType.PDFPLUMBER  # Fast default

    # service
    SERVICE_NAME: str = "doc_ingestion_service"

    # Logging Configuration
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE_PATH: str = f"logs/{SERVICE_NAME}.log"
    # LOKI_URL: str | None = None  # e.g., "http://localhost:3100/loki/api/v1/push"
    LOKI_URL: str = "http://localhost:3100/loki/api/v1/push"

    # Observability
    # OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None  # e.g., "http://localhost:4317"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "localhost:4317"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM Provider Flags
    EMBEDDING_PROVIDER: str = "ollama"  # Options: "ollama", "openai", etc.
    VECTOR_STORE_PROVIDER: str = "qdrant"  # Options: "qdrant", "pgvector", etc.

    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text:v1.5"

    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Qdrant collections
    PDF_INGESTION_VECTOR_NAME: str = "pdf_documents"
    PDF_INGESTION_VECTOR_TEST_NAME: str = "test_pdf_documents"

    # Ingestion & Chunking Strategy
    PARENT_CHUNK_SIZE: int = 600
    PARENT_CHUNK_OVERLAP: int = 100
    CHILD_CHUNK_SIZE: int = 150
    CHILD_CHUNK_OVERLAP: int = 25
    TOKENIZER_ENCODING_NAME: str = "cl100k_base"

settings = Settings()
