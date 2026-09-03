import asyncio
import io
from typing import AsyncIterator
from pypdf import PdfReader

# ==========================================
# 1. Asynchronous PDF Stream Reader
# ==========================================
async def stream_pdf_pages(pdf_stream: io.BytesIO) -> AsyncIterator[str]:
    """Reads a PDF byte stream and yields text page by page asynchronously."""
    loop = asyncio.get_running_loop()

    # Offload PDF initialization to a thread pool (CPU-bound task)
    reader = await loop.run_in_executor(None, PdfReader, pdf_stream)

    for page in reader.pages:
        # Offload text extraction to a thread pool (CPU-bound task)
        text = await loop.run_in_executor(None, page.extract_text)

        yield text or ""  # Ensure we return empty string if text is None

        # Yield control back to the event loop momentarily between pages
        await asyncio.sleep(0)


# ==========================================
# 2. Asynchronous Processing/Chunking Method
# ==========================================
async def create_chunks_async(text: str, chunk_size: int = 500) -> list[str]:
    """Simulates an asynchronous method that processes and chunks text."""
    # Simulate a small I/O or processing delay
    await asyncio.sleep(0.05)

    # Simple character-based splitting logic
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks


# ==========================================
# 3. Execution Main Program
# ==========================================
async def main():
    # Replace 'example.pdf' with the path to your actual PDF file
    try:
        with open("example.pdf", "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        print("Error: 'example.pdf' not found. Please provide a valid file.")
        return

    # Convert raw bytes into an in-memory stream
    pdf_stream = io.BytesIO(pdf_bytes)

    print("Starting pipeline: Streaming PDF and chunking asynchronously...\n")

    page_number = 1

    # 'async for' waits for each page to be extracted sequentially without blocking
    async for page_text in stream_pdf_pages(pdf_stream):
        print(f"=== Page Number: {page_number} ===")
        print(f"Raw Text Length: {len(page_text)} characters")

        # 'await' the asynchronous chunking operation for the current page
        page_chunks = await create_chunks_async(page_text, chunk_size=300)

        print(f"Generated Chunks: {len(page_chunks)} chunks created.")

        # Show a quick snippet of the first chunk if available
        if page_chunks:
            snippet = page_chunks[0].replace("\n", " ")[:60]
            print(f"First Chunk Preview: {snippet}...")

        print("-" * 40 + "\n")
        page_number += 1


if __name__ == "__main__":
    # Standard entry point to kick off the async event loop
    asyncio.run(main())
