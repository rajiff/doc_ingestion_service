import io
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.services.pdf_ingestion_service import PDFIngestionService
from app.schemas.doc_ingestion import DocPageExtraction, DocIngestionResponse
from app.interfaces.base_parser import BasePDFParser
from app.interfaces.base_chunker import BaseChunker
from app.interfaces.base_embedder import BaseEmbeddingService
from app.interfaces.base_vector_store import BaseVectorStore


class DummyChunk:
    """Lightweight stub representing chunk outputs from chunker."""
    def __init__(self, text: str, page_number: int, parent_id: str = None):
        self.text = text
        self.page_number = page_number
        self.parent_id = parent_id


@pytest.fixture
def mock_parser():
    """mock parser """
    parser = MagicMock(spec=BasePDFParser)
    parser.extract_text.return_value = [
        DocPageExtraction(page_number=1, text="Sample document page text content.")
    ]
    return parser


@pytest.fixture
def mock_chunker():
    chunker = MagicMock(spec=BaseChunker)
    parent_chunk = DummyChunk("Sample document page text content.", page_number=1)
    child_chunk = DummyChunk("Sample document page", page_number=1, parent_id="parent-uuid-1")

    chunker.split_pages.return_value = ([parent_chunk], [child_chunk])
    return chunker


@pytest.fixture
def mock_embedder():
    embedder = MagicMock(spec=BaseEmbeddingService)
    # Async mock for generating 1 dummy vector for 1 child chunk
    embedder.embed_documents = AsyncMock(return_value=[[0.1] * 768])
    return embedder


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=BaseVectorStore)
    store.find_by_client_doc_id = AsyncMock(return_value=None)
    store.delete_by_client_doc_id = AsyncMock(return_value=None)
    store.upsert_points = AsyncMock(return_value=None)
    return store


@pytest.fixture
def ingestion_service(mock_parser, mock_chunker, mock_embedder, mock_vector_store):
    return PDFIngestionService(
        parser=mock_parser,
        chunker=mock_chunker,
        embedder=mock_embedder,
        vector_store=mock_vector_store
    )


@pytest.fixture
def sample_pdf_stream():
    """Generates a dummy binary stream imitating an uploaded file."""
    content = b"%PDF-1.4 Fake PDF Content stream for integration test"
    stream = io.BytesIO(content)
    return stream


# --- Integration Test Cases ---

@pytest.mark.asyncio
async def test_successful_document_ingestion(
    ingestion_service,
    mock_vector_store,
    sample_pdf_stream
):
    """Test standard happy path for a new document ingestion."""
    client_doc_id = "DOC_TEST_001"

    response = await ingestion_service.ingest_document(
        file_stream=sample_pdf_stream,
        client_doc_id=client_doc_id,
        force_reingest=False
    )

    # Assertions on API Response Contract
    assert isinstance(response, DocIngestionResponse)
    assert response.status == "success"
    assert response.client_doc_id == client_doc_id
    assert response.parent_chunks_indexed == 1
    assert response.child_chunks_indexed == 1
    assert len(response.checksum) == 64  # SHA-256 length

    # Verify Vector Store Integration Calls
    mock_vector_store.find_by_client_doc_id.assert_called_once_with(
        collection_name="test_documents",
        client_doc_id=client_doc_id
    )
    mock_vector_store.upsert_points.assert_called_once()


@pytest.mark.asyncio
async def test_idempotent_ingestion_skips_processing(
    ingestion_service,
    mock_vector_store,
    sample_pdf_stream
):
    """Test that submitting an identical file skips re-indexing."""
    client_doc_id = "DOC_TEST_001"

    # Calculate checksum upfront to mock vector store returning matching hash
    import hashlib
    expected_checksum = hashlib.sha256(sample_pdf_stream.getvalue()).hexdigest()

    mock_vector_store.find_by_client_doc_id.return_value = {
        "checksum": expected_checksum,
        "parent_count": 1,
        "child_count": 1
    }

    response = await ingestion_service.ingest_document(
        file_stream=sample_pdf_stream,
        client_doc_id=client_doc_id,
        force_reingest=False
    )

    assert response.status == "skipped"
    assert response.checksum == expected_checksum
    # Verify we did NOT execute vector storage upserts
    mock_vector_store.upsert_points.assert_not_called()


@pytest.mark.asyncio
async def test_force_reingest_overwrites_existing(
    ingestion_service,
    mock_vector_store,
    sample_pdf_stream
):
    """Test that force_reingest=True deletes existing points before upserting."""
    client_doc_id = "DOC_TEST_001"

    import hashlib
    expected_checksum = hashlib.sha256(sample_pdf_stream.getvalue()).hexdigest()

    # Simulate existing doc in Qdrant
    mock_vector_store.find_by_client_doc_id.return_value = {
        "checksum": expected_checksum,
        "parent_count": 1,
        "child_count": 1
    }

    response = await ingestion_service.ingest_document(
        file_stream=sample_pdf_stream,
        client_doc_id=client_doc_id,
        force_reingest=True  # Force overwrite
    )

    assert response.status == "success"
    # Verify deletion was called before upserting
    mock_vector_store.delete_by_client_doc_id.assert_called_once_with(
        collection_name="test_documents",
        client_doc_id=client_doc_id
    )
    mock_vector_store.upsert_points.assert_called_once()


@pytest.mark.asyncio
async def test_ingestion_pipeline_error_handling(
    ingestion_service,
    mock_vector_store,
    sample_pdf_stream
):
    """Test that internal exceptions return a graceful failed response."""
    client_doc_id = "DOC_TEST_001"

    # Force vector store upsert to throw an infrastructure Exception
    mock_vector_store.upsert_points.side_effect = Exception("Qdrant Connection Timeout")

    response = await ingestion_service.ingest_document(
        file_stream=sample_pdf_stream,
        client_doc_id=client_doc_id,
        force_reingest=False
    )

    assert response.status == "failed"
    assert "Qdrant Connection Timeout" in response.error_details
