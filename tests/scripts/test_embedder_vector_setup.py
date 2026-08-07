import asyncio
from app.interfaces import (
    BaseEmbeddingService,
    BaseVectorStore
)
from app.core.dependency_factory import get_embedding_service, get_vector_store

# run as `uv run python -m tests.scripts.test_embedder_vector_setup`

async def main():
    """Testing embedder and vector_store"""
    # obtain it from dependency initialization
    embedder: BaseEmbeddingService = get_embedding_service()
    vector_store: BaseVectorStore = get_vector_store()

    print(f"Loaded embedder: {embedder.__class__.__name__}")
    print(f"Loaded vector store: {vector_store.__class__.__name__}")

    test_doc = "FastAPI with Qdrant and Ollama is an excellent production stack."

    print("\n1. Generating embedding via Ollama...")
    vector = await embedder.embed_query(test_doc)
    print(f"Generated Vector dimension: {len(vector)}")

    dimension = await embedder.dimension

    print("\n2. Ensuring Qdrant Collection...")
    await vector_store.create_collection(
        "test_temp_collection",
        vector_size=dimension
    )

    print("\n3. Upserting Test Point...")
    await vector_store.upsert_vectors(
        collection_name="test_temp_collection",
        vectors=[vector],
        payloads=[{"text": test_doc, "source": "unit_test"}]
    )

    print("\n4. Executing Similarity Search...")
    results = await vector_store.search(
        "test_temp_collection",
        query_vector=vector,
        top_k=1
    )

    print("\nSearch Result:", results)

if __name__ == "__main__":
    asyncio.run(main())
