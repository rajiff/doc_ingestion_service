# Project Overview: PDF Ingestion Service

## Summary
A FastAPI microservice designed to ingest, parse, chunk, and embed PDF documents for use in retrieval-augmented generation (RAG) systems. It supports multiple parsing strategies and a parent-child chunking hierarchy.

## Core Functionalities
1.  **Multi-Strategy Parsing:** Uses an abstraction layer (`BasePDFParser`) to switch between different parsing engines (e.g., `PyPDF`, `PDFPlumber`) at runtime via configuration.
2.  **Data Validation & Sanitization:** Employs Pydantic schemas to validate and clean extracted text/metadata before any downstream processing.
3.  **Chunking Service:** Implements a **Parent-Child Chunking** strategy, where large documents are split into smaller "Child" chunks (for retrieval) while maintaining links to the "Parent" context.
4.  **Embedding & Vector Storage:** Integrates with an embedding service (OpenAI-compatible, supporting Ollama) and persists vectors/payloads into **Qdrant**.
5.  **Full Observability:** Integrated with OpenTelemetry, Prometheus, and Jaeger for tracing and metrics.

## Functional Flow: Ingestion Pipeline
The system follows a linear processing pipeline during the `Write Path`:
1.  **Input & Extraction:** File upload $\rightarrow$ Identification of Parser $\rightarrow$ Raw Text Extraction.
2.  **Sanitization:** Cleaning of extracted text content.
3.  **Chunking Service:** Splitting text into Parent/Child nodes with UUID-based linking.
4.  **Embedding:** Vector generation for each Child chunk.
5.  **Persistence:** Upserting vectors and payload (including `client_doc_id`, `page_number`, `text_content`, and `checksum`) to Qdrant.

## Data Modeling Strategy
*   **Vector Embedding:** Derived **ONLY** from the specific chunk text for efficient similarity search.
*   **Payload / Metadata Storage:** Stores full context, including:
    - `client_doc_id`
    - `chunk_id` & `parent_id`
    - `page_number`
    - `text_content` (The actual chunk text)
    - `checksum`

## Tech Stack
- **Backend:** FastAPI, Python
- **Manager/Task Runner:** `uv`
- **Vector Database:** Qdrant
- **Observability:** OpenTelemetry, Prometheus, Jaeger, Grafana
- **Deployment:** Docker Compose