# Design Review: PDF Ingestion Service (Architecture)

## Summary
This document captures architectural reviews and design decisions for the PDF Ingestion microservice, focusing on scalability, maintainability, and RAG-specific performance characteristics.

---

## [Review #1] Architecture & Pipeline Scalability
**Date:** 2026-08-12
**Status:** Reviewed - Actionable Recommendations Provided

### 1. Architectural Strengths
*   **Strategy Pattern Adherence:** The `BasePDFParser` abstraction ensures the system remains compliant with the Open-Closed Principle, allowing for easy expansion of parsing logic without modifying core ingestion flows.
*   **Contextual Integrity (Parent-Child Chunking):** The decision to decouple retrieval units (Children) from context containers (Parents) is the industry standard for high-quality RAG, preventing the "lost in-the-middle" problem common with flat chunking.
*   **Strict Domain Boundaries:** The separation of Transport (API), Business Logic (Services), and Strategy (Parsers) allows for independent testing of the extraction logic without mock HTTP objects.

### 2. Identified Risks & Weaknesses
*   **Synchronous Processing Bottleneck:** Currently, long-running parsing/chunking tasks run within the FastAPI request context. Large files or complex layouts may cause gateway timeouts (504s).
*   **Payload Coupling:** There is a risk of "Schema Drift" if individual parsers return varying metadata formats that the `IngestionService` isn't prepared to handle consistently.
*   **Sequential Execution:** The current pipeline (Sanitization $\rightarrow$ Chunking $\rightarrow$ Embedding) processes chunks sequentially, which ignores opportunities for parallel-processing adjacent tasks like embedding generation.

### 3. Alternatives & Trade-offs Analysis

| Feature | Current Design (Sync/Sequential) | Recommended Alternative (Async Task Queue) |
| :--- | :--- | :--- |
| **User Experience** | Immediate response (for small files). | `202 Accepted` with Job ID / Polling. |
| **Scalability** | Vertical (Worker scaling). | Horizontal (Distributed worker pool). |
| **Fault Tolerance** | Difficult to resume partial jobs. | Native retries and persistence of state. |
| **Complexity** | Low (Straightforward API routes).
| **Total Cost** | Lower initial dev cost. | Higher infra-complexity for high volume. |

### 4. Proposed Solution: Stream-Processing & Transactional Integrity
*To address the Synchronous Processing Bottleneck while maintaining Memory Safety, we transition to a Streaming architecture.*

#### The "Stream" Design:
Instead of processing an entire file as one batch, we process pages individually as they are yielded from the parser. This ensures that only one page is held in memory at any given time.

#### Handling Data Integrity (All-or-Nothing):
Because Vector Databases and LLM Embedding APIs do not support ACID transactions, we implement a **Stateful Rollback** mechanism:
*   **The Session ID:** Every-page/chunk processed in a single-requesting stream is tagged with a unique `session_id`.
*   **Pending vs. Active Status:** All records are initially written to the vector store as `pending`.
*   **Commit:** Once the entire stream (all pages) has been successfully processed, all records associated with that `session_id` are updated to `active`.
*   **Rollback (Abort):** If any single page fails during processing, we catch the exception and **delete all pending records** associated with that specific `session_id`. This ensures no partial data remains in the database for a failed upload.

---

## [Review #2] Streaming vs. Batch Memory Analysis
**Date:** 2026-08-14
**Status:** Reviewed - Technical Strategy Confirmed

### Critical Design Decision: Lazy Evaluation over List Accumulation
*   **Analysis:** A common mistake in "streaming" implementations is reading the entire file into memory and simply returning a list. We have explicitly rejected this to ensure that only one page is held in memory at any given time during processing.
*   **Implementation Path:** The `BasePDFParser` will provide an `extract_pages_stream` method yielding `DocPageExtraction` objects.
*   **Impact:** This architecture ensures the system can handle documents of virtually unlimited size (limited only by single-page complexity) without OOM errors.

### Proposed Implementation Plan for Stream Processing:
1.  **Interface Extension:** Add `extract_pages_stream` to `BasePDFParser`.
2.  **Multi-Stage Processing:** The **Processing Service** will act as the orchestrator, iterating over the parser's stream and coordinating with the Chunking and Embedding services.

### Final Recommendation:
This-by-page processing ensures that we maintain memory safety while achieving high performance for large documents by avoiding batch loading of entire file contents into memory at any single point in time.
