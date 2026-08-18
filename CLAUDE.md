# CLAUDE.md - PDF Ingestion Service

## Project Context
A production-grade microservice designed to ingest, parse, and chunk PDF documents for a RAG (Retrieval-Augmented Generation) pipeline. The system supports multiple parsing strategies, high-integrity sanitization, and a Parent-Child chunking hierarchy to preserve contextual integrity in vector search results.

## Tech Stack
- **Language:** Python 3.x
- **Framework:** FastAPI
- **Package Management:** `uv` (Preferred over pip)
- **Vector Database:** Qdrant
- **Observability:** OpenTelemetry, Prometheus, Jaeger
- **Parsing Engines:** PyPDF, PDFPlumber

## Directory Map
- `app/api/`: Request handling and Dependency Injection (Keep this layer thin).
- `app/core/`: Configuration (`config.py`) and custom exceptions.
- `app/interfaces/`: Abstract Base Classes (ABCs) for parsing strategies.
- `app/parsers/`: Concrete parsing implementations.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/services/`: Core business logic (Sanitization, Chunking, Embedding).
- `tests/`: Test suite mirroring the application structure.

## Development Commands
| Action | Command |
| :--- | :--- |
| **Sync Dependencies** | `uv sync` |
| **Run Application** | `uv run uvicorn app.main:app --reload` |
| **Run Tests** | `uv run pytest` |
| **Linting Check** | `uv run pylint app/**/*.py` |
| **Documentation** | `http://localhost:8000/docs` (Swagger UI) |

## Architectural & Behavioral Constraints
- **Domain Separation:** Always keep business logic in `services`. The API layer should only handle transport concerns.
- **Strategy Pattern:** Any new parsing logic *must* be implemented as a new class in `parsers/` conforming to the `BasePDFParser` interface.
- **Validation First:** All input data must be validated via Pydantic schemas before reaching the service layer.
- **Parent-Child Chunking:** Never flatten chunks; always maintain the parent-child relationship for contextual retrieval.
- **Sanitization Flow:** Ensure sanitization happens *after* extraction but *before* chunking/embedding to avoid processing noise.
- **Observability:** All core service methods should be instrumented via OpenTelemetry where complex logic or external calls (EMBED/Parsing) are involved.
