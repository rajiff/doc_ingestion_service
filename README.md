# Document ingestion spike

Project Overview

  The PDF Ingestion Service is a FastAPI-based microservice designed to ingest PDF documents, extract their content, chunk the text into meaningful segments (Parent-Child hierarchy),
  generate embeddings, and store them in a vector database (Qdrant).

  Core Functionalities

  1. Multi-Strategy Parsing: It uses an abstraction layer (BasePDFParser) allowing it to switch between different parsing engines (like PyPDF and PDFPlumber) dynamically at runtime via
  configuration.
  2. Data Validation & Sanitization: Uses Pydantic schemas to ensure that extracted text and metadata are validated before any downstream processing occurs.
  3. Chunking Service: A component that transforms raw extracted pages into "Parent-Child" token boundaries. This ensures that while small chunks are indexed for retrieval, the larger
  parent context is preserved.
  4. Embedding & Vector Storage (Planned/In-progress): An extensible embedding service (supporting local Ollama instances) to generate vector representations of text segments and upsert
  them into a Qdrant database.
  5. Observability: Built-in support for OpenTelemetry, Prometheus metrics, and Jaeger tracing, with integrated Grafana dashboarding capability.

  Functional Flow: The Ingestion Pipeline

  The system follows a linear processing pipeline when a user uploads a document:

  1. Input & Extraction:
    - User uploads a PDF via the /api/v1/ingest endpoint.
    - The service identifies the correct parser (e.g., PyPDFParser) and extracts raw text from the file.
  2. Sanitization: The extracted text is cleaned of unwanted artifacts or noise.
  3. Chunking:
    - The ParentChildChunker processes the sanitized text.
    - It splits the text into smaller "Child" chunks while maintaining a link to the larger "Parent" body (using UUIDs).
  4. Embedding:
    - For each Child chunk, the Embedding Service generates a vector representation.
  5. Persistence:
    - The system saves the vectors and metadata (including client_doc_id, page_number, text_content, and a checksum) to the Qdrant database.

  Data Modeling

  A critical distinction in the design is what gets "Embedded" vs. what stays in "Metadata":
  - Vector Embedding: Generated only from the specific chunk text for efficient similarity searching.
  - Payload/Metadata: Contains the full context, including client_doc_id, parent_id, and the text_content of the chunk.

  Tech Stack & Infrastructure

  - Framework: FastAPI (Python)
  - Package Management: uv / pip
  - Databases/Vector Store: Qdrant, Prometheus (Metrics), Jaeger (Tracing), Tempo (Storage).
  - Infrastructure: Docker-compose for deployment, Uvicorn as the ASGI server.

### ROJECT.md
Describes the PROJECT for AI agents

comprehensive summary of the system, including functional flows (Extraction $\rightarrow$ Sanitization $\rightarrow$ Chunking $\rightarrow$ Embedding $\rightarrow$
Storage), data modeling strategies (Embedding vs. Metadata), and technical stack.

- Describes the project overview, high-level scope.
- Outlines ingestion-pipeline with step-by-step execution flow.
- Data modeling guidelines for what gets embedded vs. stored as metadata.

### DESIGN.md
DESIGN.md is authored from the perspective of a Principal Software Engineer.

The document covers:
- Architectural Philosophy: The layered approach and separation of concerns between API, Services, and Parsers.
- Design Patterns: Explanation of the Strategy Pattern for parsing and why it was chosen over conditionals (Open-Closed Principle).
- RAG Specifics: Detailed rationale for the Parent-Child chunking strategy and the distinction between "Embedding" vs "Metadata."
- Data Integrity: The importance of sanitization and checksums in LLM pipelines.
- Operational Excellence: How OpenTelemetry provides observability across the ingestion lifecycle.

### CLAUDE.md
CLAUDE.md file is at the project root.

  This file serves as a "contract" and reference for Claude Code, ensuring that all future interactions adhere to the established architectural standards:
  - Contextual Awareness: Clearly defines the RAG-focused purpose of the service.
  - Tooling & Tech Stack: Explicitly specifies uv for dependency management and identifies the core tech stack (FastAPI, Qdrant, OpenTelemetry).
  - Navigation Map: Provides a clear directory map to help navigate between layers (Services vs. Parsers).
  - Behavioral Constraints: Enforces the Strategy Pattern, Pydantic-first validation, and the specific Parent-Child Chunking logic as mandatory constraints for any code modifications or
  features added during this session.



## Day 1: Interface Design, FastAPI Setup & Text Extraction Layer

#### Day 1 Deliverables & Tasks
- The Skeleton: Build a clean FastAPI microservice skeleton adhering to strict domain boundaries (/interfaces, /services, /parsers, /routers).
- The Abstraction: Write the BasePDFParser abstract base class using Python's native abc module to strictly honor the Open-Closed Principle.
- The Strategies: Implement two concrete parsers—PyPDFParser and PDFPlumberParser—that fulfill the base interface.
- The Endpoint: Code the POST /api/v1/ingest endpoint to accept file uploads in-memory and dynamically switch between your parsing engines via a runtime configuration flag.
- The Guardrail: Define the robust Pydantic schemas to shape, sanitize, and validate the extracted text and core metadata (e.g., filename, page_number, cleaned_text) before any downstream processing happens.

### Project layout (initial )

```plaintext
pdf_ingestion_service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization & global middleware
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic-settings for runtime configurations
│   │   └── exceptions.py       # Global exception handlers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependency injection (e.g., getting parser instances)
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── ingest.py       # POST /api/v1/ingest endpoint
│   │
│   ├── interfaces/
│   │   ├── __init__.py
│   │   └── base_parser.py      # Abstract Base Class (BasePDFParser)
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pypdf_parser.py     # PyPDF concrete strategy
│   │   └── pdfplumber_parser.py# PDFPlumber concrete strategy
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ingestion.py        # Pydantic schemas (ExtractionRequest/Response/Metadata)
│   │
│   └── services/
│       ├── __init__.py
│       └── ingestion_service.py# Orchestrates the parser strategy and sanitization
│
├── tests/                      # Unit and integration tests mirroring app structure
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/
│   └── parsers/
│
├── .env.example
├── requirements.txt
└── README.md
```

## Running the Application

### 1. Install Dependencies
First, ensure all dependencies are installed:

```bash
uv sync
# OR if you don't have uv set up as a tool
pip install -e .
```

### 2. Run the Application
You can run the application using `uvicorn`. Since the FastAPI app is defined in `app/main.py`, you should point it to the app object:

```bash
# Using uvicorn directly
uv run uvicorn app.main:app --reload
```

- `app.main`: Points to the app.py module inside the `app` directory.
- `app`: Refers to the app instance created in `app/main.py`.
- `--reload`: Enables hot-reloading for development.

### 3. Accessing the API
Once the server is running (usually on `http://127.0.0.1:8000`), you can access the following endpoints:

- Interactive Documentation: Visit `http://127.0.0.1:8000/docs` to see the Swagger UI.
- Health Check: `GET http://127.0.0.1:8000/health`
- Ingest Endpoint: `POST http://127.0.0.1:8000/api/v1/ingest`

### 4. Example Test Request
You can test the ingestion endpoint using curl and one of your sample files:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@tests/test_docs/SOLID Principles Baeldung.pdf"
```

### 5. Run test cases
You can run test cases

```bash
uv run pytest
```

### 6. Run Lint check
To perform lint check, run this command, project TOML file has the configurations to ignore tests and other not needed folder

```bash
uv run pylint app/**/*.py
```

## Observability

| Service       	| Access URL / Port      	| Description                                                     	|
|---------------	|------------------------	|-----------------------------------------------------------------	|
| FastAPI App   	| http://localhost:8000  	| Microservice pointing to OTel Collector (http://localhost:4317) 	|
| Jaeger UI     	| http://localhost:16686 	| Dedicated Jaeger Tracing UI                                     	|
| Grafana UI    	| http://localhost:3030  	| Consolidated dashboard (Jaeger, Tempo, Loki, Prometheus)        	|
| Prometheus UI 	| http://localhost:9090  	| Raw Metrics Explorer                                            	|


## Day 2: Production-Grade Chunking & Pluggable Embedding Strategies

#### Day 2 Deliverables & Tasks
- Deliverable: The text splitting service that transforms raw pages into explicit Parent-Child token boundaries.
- Tasks:
  - Implement a token-aware ParentChildChunker service. The text is split into overlapping child nodes linked by a distinct parent_id uuid to the larger textual body.
  - Define the pluggable embedding interface using the OpenAI-compatible client standard, mapping directly to your local Ollama engine via configuration.
  - Wrap this step with initial Ariadne Phoenix or LangSmith instrumentation so you can visualize the graph of how your text splits into semantic blocks.


### Chunking & Embedding Lifecycle (When and Where)
Understanding the lifecycle sequence prevents unnecessary database hits or redundant computations.
```plaintext
                            [INGESTION PHASE (Write Path)]

            User Upload -> Extract Raw Text -> Sanitize/Clean Text
                                         |
                                         ▼
                                  Chunking Service
                      (Splits text into Parent & Child Chunks)
                                         │
                                         ▼
                                 Embedding Service
                     (Calls embed_documents on Child Chunks)
                                         │
                                         ▼
                             Vector Store Service
          (Upserts Child Vectors + Payload containing Parent Text & Metadata)

      -------------------------------------------------------------------------

                         [RETRIEVAL PHASE (Read Path)]

User Query -> Embedding Service (Calls embed_query) -> Vector Search in Qdrant
```


### Metadata Strategy & What Gets Embedded
Helps understand what actually goes into the embedding, and what goes into metadata?

```plaintext
   +-------------------------------------------------------------+
   |                       DOCUMENT CHUNK                        |
   |                                                             |
   |  +-------------------------------------------------------+  |
   |  |                   VECTOR EMBEDDING                    |  |
   |  |  [0.012, -0.453, 0.891, ... 768 float values]         |  |
   |  |  Source: Derived ONLY from chunk_text                 |  |
   |  +-------------------------------------------------------+  |
   |                                                             |
   |  +-------------------------------------------------------+  |
   |  |               PAYLOAD / METADATA STORAGE              |  |
   |  |  - client_doc_id : "LMS_101_DOC_A"                    |  |
   |  |  - chunk_id      : "uuid-v5-123"                      |  |
   |  |  - parent_id     : "uuid-v5-parent-01"                |  |
   |  |  - page_number   : 3                                  |  |
   |  |  - text_content  : "This is the actual text chunk..." |  |
   |  |  - checksum      : "a1b2c3d4..."                      |  |
   |  +-------------------------------------------------------+  |
   +-------------------------------------------------------------+
```


## Observability (Trace, Metrics, Logs for Diagnosing & Monitoring)
Use standard observability for system health, and AI-native observability for semantic and RAG quality.

- Instrumentation is a platform concern. Observability products are downstream consumers.
- Instrument once where possible, export to multiple backends.

```plaintext
                 APPLICATION CODE
                        │
                        │  ONE primary instrumentation model
                        ▼
        ┌───────────────────────────────────┐
        │ OpenTelemetry + AI Semantic Model │
        │                                   │
        │ Standard OTel SemConv             │
        │ + OpenInference where needed      │
        └─────────────────┬─────────────────┘
                          │ OTLP
                          ▼
                OpenTelemetry Collector
                          │
          ┌───────────────┼──────────────────┐
          │               │                  │
          ▼               ▼                  ▼
      Langfuse         Phoenix         Grafana Stack
      AI traces        RAG analysis    Metrics/Logs/Traces
      Prompts          Evaluation      Prometheus/Tempo/Loki
      Cost             Experiments
```

```plaintext
                    ┌─────────────────────────────┐
                    │       RAG Application       │
                    │  API / Agent / Workflow     │
                    └──────────────┬──────────────┘
                                   │
                    OpenTelemetry / OpenInference
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
     Infrastructure          AI / LLM Tracing       Business Metrics
       Observability          & Evaluation
             │                     │                     │
   Prometheus / Grafana    Langfuse / Phoenix      Product Analytics
   Datadog / New Relic     LangSmith / Arize       Custom KPIs
             │                     │
             └──────────────┬──────┘
                            ▼
                     Alerting / SRE
```

Observability has to be designed at multiple, different layers, the layered distinction matters enormously.

```plaintext
OpenTelemetry       = Telemetry foundation
OpenInference       = AI-oriented instrumentation/semantic conventions
OpenLLMetry         = Convenient instrumentation implementation
Langfuse            = AI observability backend
Phoenix             = AI/RAG observability and evaluation backend
Grafana Stack       = General infrastructure observability backend
```
