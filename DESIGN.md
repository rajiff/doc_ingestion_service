# Architectural Design: PDF Ingestion & Processing Service

## Context & Vision
The goal of this service is to provide a robust, production-grade ingestion pipeline for converting unstructured PDF documents into structured, chunked, and embedded data suitable for Retrieval-Augmented Generation (RAG) systems. 

This document outlines the architectural decisions, patterns, and technical trade-offs made during the initial implementation. This is intended as a **living document** to guide future contributors and clarify why we chose specific paths over alternatives.

---

## High-Level Architecture
We utilize a **layered architecture** approach to maintain strict domain boundaries:

1.  **API/Transport Layer (`/api`):** FastAPI handles request/response handling, schema validation (Pydantic), and Dependency Injection (DI). It is intentionally thin; it delegates all business logic to the Services layer.
2.  **Service Layer (`/services`):** The core domain logic resides here. This includes **Sanitization**, **Chunking**, and **Embedding Orchestration**. 
3.  **Domain Logic/Parser Layer (`/parsers` & `/interfaces`):** Contains the strategy-specific implementations for document extraction.
4.  **Schema & Models Layer (`/schemas`):** Centralizes all data transfer objects (DTOs) and ensures type safety across boundaries.

---

## Core Architectural Patterns

### 1. The Strategy Pattern (Parsing Engine)
Instead of a monolithic parser with complex conditional logic, we use the **Strategy Pattern**. By defining `BasePDFParser` as an Abstract Base Class (ABC), we adhere to the Open-Closed Principle:
- **Why:** Adding support for a new PDF type (e.g., OCR-heavy vs. text-based) should require adding a new class, not modifying existing code in the Ingestion Service.
- **How:** The `IngestionService` consumes an implementation of `BasePDFParser` at runtime based on configuration/metadata.

### 2. Parent-Child Chunking Strategy
One of the primary challenges in RAG is "context loss"—small chunks are great for finding, but they lack sufficient context to answer complex questions.
- **Design Choice:** We implement a **Parent-Child hierarchy**.
- **Mechanism:** Text is split into "Children" (the search units) and associated with a "Parent" (the contextual container). 
- **Rationale:** During retrieval, we locate the small child chunk but provide the larger parent context to the LLM. This preserves semantic integrity while maintaining high search precision.

### 3. Data Integrity & Sanitization
LLMs are sensitive to noise in the input data (e.g., page numbers, headers/footers, and boilerplate text).
- **The Guardrail:** We enforce a strict sanitization step after extraction but *before* chunking.
- **Consistency:** We use checksums for every processed unit to ensure that if the raw file changes, we can detect out-of-sync indices in the vector store.

---

## Data Management & Storage Strategy

### Vector vs. Metadata Distinction
We differentiate clearly between what is "Searchable" and what is "Readable":

| Component | Content Source | Purpose |
| :--- | :--- | :--- |
| **Vector Embedding** | `chunk_text` (Child only) | Dimensionality-reduced representation for similarity search. |
| **Payload/Metadata** | Full context + IDs | The actual "Knowledge" retrieved after the match is found. |

- **Rationale:** Embedding large blocks of text (Parents) yields poor similarity scores. By embedding only the Child chunks but storing the Parent content in metadata, we get the best of both worlds: precise search and rich context.

---

## Processing Architecture: Streaming & Transactional Integrity

### The `PDFStreamIngestionService`
To support large documents without hitting memory limits, we implement a **Streaming Pipeline** approach. Instead of processing an entire file as one batch, we process pages individually as they are yielded from the parser stream.

#### Stream-Processing Flow (Per Page):
1.  **Stream Extraction:** The `parser` yields a `DocPageExtraction` object for each page found in the file.
2.  **Chunking & Embedding:** As soon as a single page is extracted, it is passed to the Chunking and Embedding services immediately.
3.  **Persistence:** Only after individual chunk embedding is successful do we persist that data to the vector store.

#### "All-or-Nothing" Transactional Integrity (Stateful Rollback)
Because Vector Databases and LLM Embedding APIs do not support ACID transactions, we implement a **Stateful Rollback** mechanism:
*   **The Session ID:** Every-page/chunk processed in a single-requesting stream is tagged with a unique `session_id`.
*   **Pending vs. Active Status:** All records are initially written to the vector store with a `pending` status.
*   **Commit:** Once the entire stream (all pages) has been successfully processed, all records associated with that `session_id` are updated to `active`.
*   **Rollback (Abort):** If any single page fails during processing, we catch the exception and **delete all pending records** associated with that specific `session_id`. This ensures no partial data remains in the database for a failed upload.

---

## Operational Excellence & Observability
This service is designed to be "production-ready" from inception through **OpenTelemetry** integration.

- **Trace Propagation:** Every request/ingestion job produces a trace ID that flows through the parser, chunker, and embedding service. This allows us to pinpoint exactly where latency or errors occur (e.g., *is the PDF parser slow, or is the Embedding API hanging?*).
- **Metrics:** We expose Prometheus metrics for ingestion rates, failure types (Parser vs. Network), and processing time per page.

---

## Evolutionary Roadmap & Technical Debt
- **Scale:** The current Streaming implementation handles large files by keeping memory usage linear to the size of a single page rather than the whole file. For extremely high-volume/Gigabyte-sized files, we will eventually move this to an asynchronous Task Queue (e.g., Celery).
- **Parsing Diversity:** As we encounter complex layouts (multi-column, tables), we may need to evolve from `BasePDFParser` to a more modular "Element Extraction" model where layout analysis is a pre-processing step.

## Guidelines for Contributors
1.  **Never modify `parsers/` directly without checking `interfaces/`.** Ensure any new parser strictly satisfies the contract.
2.  **Pydantic is our source of truth.** If you add a field to an extraction response, it must be reflected in the Schema immediately.
3.  **Keep Services Pure.** The `services/` layer should not know about HTTP status codes or specific API route details. It should work with Data Objects and return Success/Failure results.
