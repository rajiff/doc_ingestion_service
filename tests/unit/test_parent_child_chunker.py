import pytest
import tiktoken
from app.services.parent_child_chunker import ParentChildChunker
from app.schemas.chunk import ParentChunk, ChildChunk

# This is a unit test case
# run as `uv run pytest tests/unit/test_parent_child_chunker.py -v -s `

@pytest.fixture
def tokenizer():
    """Default BPE encoding"""
    return tiktoken.get_encoding("cl100k_base")

@pytest.fixture
def default_chunker():
    """Chunker object"""
    return ParentChildChunker(
        parent_chunk_size=100,
        parent_chunk_overlap=20,
        child_chunk_size=30,
        child_chunk_overlap=5,
        encoding_name="cl100k_base",
    )

def test_chunk_text_parent_child_relationships(default_chunker):
    """Verify parent chunks contain children and parent_id foreign keys match."""
    sample_text = "FastAPI with Qdrant and Ollama is a production-grade RAG stack. " * 30
    metadata = {"doc_id": "test_123", "author": "dev"}

    parent_chunks = default_chunker.chunk_text(sample_text, metadata=metadata)

    assert len(parent_chunks) > 0

    for parent in parent_chunks:
        assert isinstance(parent, ParentChunk)
        assert parent.parent_id is not None
        assert parent.token_count <= default_chunker.parent_chunk_size
        assert parent.metadata["doc_id"] == "test_123"
        assert len(parent.children) > 0

        for child in parent.children:
            assert isinstance(child, ChildChunk)
            assert child.parent_id == parent.parent_id
            assert child.token_count <= default_chunker.child_chunk_size
            assert child.metadata["parent_id"] == parent.parent_id
            assert child.metadata["doc_id"] == "test_123"


def test_chunk_text_token_limit_compliance(default_chunker, tokenizer):
    """Ensure generated parent and child chunks do not exceed token bounds."""
    long_text = "Artificial intelligence and machine learning pipelines require precise chunking. " * 50

    parent_chunks = default_chunker.chunk_text(long_text)

    for parent in parent_chunks:
        p_tokens = len(tokenizer.encode(parent.text))
        assert p_tokens <= default_chunker.parent_chunk_size

        for child in parent.children:
            c_tokens = len(tokenizer.encode(child.text))
            assert c_tokens <= default_chunker.child_chunk_size


def test_chunk_text_short_input(default_chunker):
    """Ensure short text produces a single parent and minimal child chunks without errors."""
    short_text = "FastAPI is fast."

    parent_chunks = default_chunker.chunk_text(short_text)

    assert len(parent_chunks) == 1
    parent = parent_chunks[0]
    assert parent.text == short_text
    assert len(parent.children) == 1
    assert parent.children[0].text == short_text


def test_chunk_text_empty_input(default_chunker):
    """Empty input should return an empty list of parent chunks."""
    parent_chunks = default_chunker.chunk_text("")
    assert parent_chunks == []
