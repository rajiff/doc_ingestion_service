from typing import List, Optional, Union
import httpx
from app.interfaces.base_embedder import BaseEmbeddingService
from app.core.observability import observe

class OllamaEmbeddingService(BaseEmbeddingService):
    """
    Production-grade client wrapper for the
    local Ollama embeddings pipeline. Optimized to natively
    balance atomic vector queries alongside batched document indexing.
    """

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._dimension: Optional[int] = None

    @observe(label="get_dimension")
    async def get_dimension(self) -> int:
        """
        Dynamically detects vector dimensionality by issuing an initial probe.
        Caches the result locally to eliminate follow-up network discovery loops.
        """
        if self._dimension is None:
            probe_vector = await self.embed_query("probe")
            self._dimension = len(probe_vector)
        return self._dimension

    @observe(
        label="embed_query",
        attribute_provider=lambda ctx: {
            "len_query_to_embed":len(ctx.get("text"))
        }
    )
    async def embed_query(self, text: str) -> List[float]:
        """Encodes an isolated search query string using the
        correct model routing prefix.
        """
        # Nomic models explicitly require retrieval task optimization prefixes
        formatted_text = f"search_query: {text}" if "nomic" in self.model else text

        # Execute network call via standard singular input channel
        embeddings = await self._call_ollama_api(formatted_text)
        return embeddings[0]

    @observe(
        label="embed_documents",
        attribute_provider=lambda ctx: {
            "len_doc_to_embed":len(ctx.get("texts"))
        }
    )
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Default document passage embedding entry point. Utilizes micro-batching
        underneath to provide corporate-grade horizontal indexing throughput.
        """
        if not texts:
            return []
        return await self.embed_documents_batch(texts)

    async def embed_documents_iteratively(self, texts: List[str]) -> List[List[float]]:
        """Fallback iterative document parsing method
        for highly constraint-bound connections.
        """
        results = []
        for t in texts:
            formatted_text = f"search_document: {t}" if "nomic" in self.model else t
            vector_wrap = await self._call_ollama_api(formatted_text)
            results.append(vector_wrap[0])
        return results

    @observe(
        label="embed_documents_batch",
        attribute_provider=lambda ctx: {
            "len_doc_batch_to_embed":len(ctx.get("texts"))
        }
    )
    async def embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
        """Batches multiple document strings into a single optimized payload call."""
        formatted_texts = [
            f"search_document: {t}" if "nomic" in self.model else t
            for t in texts
        ]
        return await self._call_ollama_api(formatted_texts)

    @observe(
        label="_call_ollama_api",
        attribute_provider=lambda ctx: {
            "len_payload_input":len(ctx.get("payload_input"))
        }
    )
    async def _call_ollama_api(
            self,
            payload_input: Union[str, List[str]]
        ) -> List[List[float]]:
        """
        Core pipeline communication layer. Manages
        structural transformation of input objects to safely
        handle both strings and arrays using the /api/embed endpoint.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": payload_input
                },

                # Elevated window duration to prevent failure during heavy micro-batches
                timeout=60.0
            )
            response.raise_for_status()
            response_json = response.json()

            # The modern /api/embed endpoint returns data via
            # the "embeddings" plural matrix structure
            if "embeddings" in response_json:
                return response_json["embeddings"]

            # Fallback for structural safety variants
            if "embedding" in response_json:
                return [response_json["embedding"]]

            raise KeyError(
                f"Unexpected response schema from Ollama instance: {response_json}")
