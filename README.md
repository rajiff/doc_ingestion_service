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
| Grafana UI    	| http://localhost:3000  	| Consolidated dashboard (Jaeger, Tempo, Loki, Prometheus)        	|
| Prometheus UI 	| http://localhost:9090  	| Raw Metrics Explorer                                            	|
