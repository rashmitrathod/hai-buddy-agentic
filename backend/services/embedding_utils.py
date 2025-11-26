import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text_chunks: list[str]):
    """
    Accepts a list of strings (chunks) and returns list of embedding vectors.
    """

    # Ensure text_chunks is a list of clean strings
    clean_chunks = [chunk.strip() for chunk in text_chunks if isinstance(chunk, str) and chunk.strip()]

    if not clean_chunks:
        raise ValueError("No valid text chunks provided for embedding")

    # Call embeddings API with a list of strings
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=clean_chunks
    )

    embeddings = [item.embedding for item in response.data]

    return embeddings