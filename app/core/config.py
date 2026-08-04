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

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/ingestion_service.log"
    LOKI_URL: str | None = None  # e.g., "http://localhost:3100/loki/api/v1/push"
    # LOKI_URL: str = "http://localhost:3100/loki/api/v1/push"

    # Observability
    # OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None  # e.g., "http://localhost:4317"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "localhost:4317"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
