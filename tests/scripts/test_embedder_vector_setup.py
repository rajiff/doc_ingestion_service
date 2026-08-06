import asyncio
from app.interfaces import (
    BaseEmbeddingService,
    BaseVectorStore
)
from app.services import (
    OllamaEmbeddingService,
    QdrantVectorStore
)

async def main():
    """Testing"""

    # http://localhost:1143
    embedder: BaseEmbeddingService = OllamaEmbeddingService(
        base_url="http://localhost:11434",
        model="nomic-embed-text:v1.5"
    )

    vector_store: BaseVectorStore = QdrantVectorStore(host="localhost", port=6333)

    test_doc = "FastAPI with Qdrant and Ollama is an excellent production stack."

    print("1. Generating embedding via Ollama...")
    vector = await embedder.embed_query(test_doc)
    print(f"Generated Vector dimension: {len(vector)}")

    dimension = await embedder.dimension

    print("2. Ensuring Qdrant Collection...")
    await vector_store.create_collection(
        "test_temp_collection",
        vector_size=dimension
    )

    print("3. Upserting Test Point...")
    await vector_store.upsert_vectors(
        collection_name="test_temp_collection",
        vectors=[vector],
        payloads=[{"text": test_doc, "source": "unit_test"}]
    )

    print("4. Executing Similarity Search...")
    results = await vector_store.search(
        "test_temp_collection",
        query_vector=vector, 
        top_k=1
    )

    print("Search Result:", results)

if __name__ == "__main__":
    asyncio.run(main())
