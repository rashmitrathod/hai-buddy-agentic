def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """
    Split text into chunks for embeddings or Q&A.
    - chunk_size: max number of characters per chunk
    - overlap: number of characters overlapping between chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start = end - overlap  # overlap for context
        if start < 0:
            start = 0
    return chunks