import tiktoken

# Use OpenAI embedding tokenizer
ENCODER = tiktoken.encoding_for_model("text-embedding-3-small")

def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def chunk_text(
    text: str,
    max_tokens: int = 300,
    overlap: int = 50
) -> list[str]:
    """
    Token-based chunking for high-quality RAG.

    Args:
        text (str): full transcript text
        max_tokens (int): max tokens per chunk
        overlap (int): token overlap between chunks for context continuity

    Returns:
        list[str]: list of chunked transcript strings
    """

    tokens = ENCODER.encode(text)
    chunks = []
    start = 0
    n_tokens = len(tokens)

    while start < n_tokens:
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = ENCODER.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move pointer forward with overlap
        start = end - overlap

    return chunks