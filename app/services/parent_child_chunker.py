from typing import List, Dict, Any
import tiktoken
from app.core.logger import logger
from app.interfaces.base_chunker import BaseChunker
from app.schemas.chunk import ParentChunk, ChildChunk

# run it as `uv run pytest tests/unit/test_parent_child_chunker.py -v -s`

class ParentChildChunker(BaseChunker):
    """
    Production-grade chunking service that implements a hierarchical Parent-Child strategy.

    This strategy isolates granular text sections (Child Chunks) to drive highly accurate
    vector searches while preserving surrounding textual context (Parent Chunks) to maximize
    the synthesis performance of downstream LLMs.
    """

    def __init__(
        self,
        parent_chunk_size: int = 600,
        parent_chunk_overlap: int = 100,
        child_chunk_size: int = 150,
        child_chunk_overlap: int = 25,
        encoding_name: str = "cl100k_base"
    ):
        # encoding "cl100k_base" is used because it aligns closely with the standard local models
        # other encodings which we coudl use are "p50k_base", "gpt-40k", "gpt-50-base"

        self.parent_chunk_size = parent_chunk_size
        self.parent_chunk_overlap = parent_chunk_overlap
        self.child_chunk_size = child_chunk_size
        self.child_chunk_overlap = child_chunk_overlap

        # Load the byte-pair encoding tokenizer natively compiled in Rust
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def _split_text_by_tokens(self, text: str, size: int, overlap: int) -> List[str]:
        """
        Splits a raw text string into overlapping windowed text substrings,
        guaranteeing that every output segment adheres strictly to token capacity constraints.
        """
        # Step A: Convert the raw string into a list of integer token IDs
        tokens = self.tokenizer.encode(text)
        chunks = []
        start = 0

        # Step B: Iterate over token array using a sliding window strategy
        while start < len(tokens):
            end = min(start + size, len(tokens))
            chunk_tokens = tokens[start:end]

            # Step C: Convert the slice of token IDs back into standard, readable text
            chunks.append(self.tokenizer.decode(chunk_tokens))

            if end == len(tokens):
                break

            # Step D: Step forward by the step size (size minus overlap) to generate standard overlap
            start += size - overlap

        return chunks

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[ParentChunk]:
        """
        Main orchestration method: Accepts raw text and transforms it into an organized
        hierarchy of interconnected Parent and Child chunk schemas.
        """
        if not text.strip():
            return []

        logger.debug(
            "Processing for chunking text of len %s into %s chunks",
            len(text),
            self.parent_chunk_size
        )

        metadata = metadata or {}

        # Phase 1: Slice the root text into high-context Parent text blocks
        parent_texts = self._split_text_by_tokens(
            text, self.parent_chunk_size, self.parent_chunk_overlap
        )

        parent_chunks = []
        for p_text in parent_texts:
            # Re-verify local token boundaries for metadata validation
            p_tokens = len(self.tokenizer.encode(p_text))

            parent = ParentChunk(
                text=p_text,
                token_count=p_tokens,
                metadata=metadata.copy(),
                children=[] # Explicit initialization circumvents type-checker validation issues
            )

            # Phase 2: Slice this specific parent's text into small, highly localized child blocks
            child_texts = self._split_text_by_tokens(
                p_text, self.child_chunk_size, self.child_chunk_overlap
            )

            for c_text in child_texts:
                c_tokens = len(self.tokenizer.encode(c_text))

                child = ChildChunk(
                    parent_id=parent.parent_id,
                    text=c_text,
                    token_count=c_tokens,
                    metadata={**metadata, "parent_id": parent.parent_id}
                )
                # ignore this lint error, as it is confused with pydantic
                parent.children.append(child) # pylint: disable=no-member

            parent_chunks.append(parent)

        logger.debug(
            "Completed chunking of text of len %d into %d parent chunks",
            len(text),
            len(parent_chunks)
        )

        return parent_chunks
