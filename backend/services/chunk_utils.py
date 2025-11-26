def stream_chunks(text: str, chunk_size=500, overlap=50):
    """
    Splits text into chunks of roughly chunk_size words with overlap.
    Always yields at least one chunk even if text is very short.
    """
    # Remove extra newlines
    text = text.replace("\n\n", "\n").strip()
    if not text:
        return  # nothing to yield

    words = text.split()
    if len(words) <= chunk_size:
        yield " ".join(words)  # yield entire text as single chunk
        return

    for start in range(0, len(words), chunk_size - overlap):
        end = start + chunk_size
        yield " ".join(words[start:end])