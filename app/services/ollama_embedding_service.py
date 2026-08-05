from typing import List, Optional
import httpx
from app.interfaces import BaseEmbeddingService

class OllamaEmbeddingService(BaseEmbeddingService):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._dimension: Optional[int] = None

    async def _detect_dimension(self) -> int:
        """Dynamically detect vector dimension by sending a warm-up probe."""
        probe_vector = await self.embed_query("probe")
        return len(probe_vector)

    @property
    async def dimension(self) -> int:
        """Lazy-load and cache the embedding vector dimension."""
        if self._dimension is None:
            self._dimension = await self._detect_dimension()
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        # Prefixing queries is model-dependent (e.g., nomic requires "search_query: ")
        formatted_text = f"search_query: {text}" if "nomic" in self.model else text
        return await self._call_ollama(formatted_text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Prefixing document passages
        formatted_texts = [
            f"search_document: {t}" if "nomic" in self.model else t
            for t in texts
        ]
        return [await self._call_ollama(t) for t in formatted_texts]

    async def _call_ollama(self, prompt: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": prompt},
                timeout=30.0
            )
            res.raise_for_status()
            return res.json()["embedding"]
