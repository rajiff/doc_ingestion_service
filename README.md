# Document ingestion spike

## Day 1: Interface Design, FastAPI Setup & Text Extraction Layer

Day 1 Deliverables & Tasks
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