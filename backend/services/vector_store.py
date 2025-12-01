import os
import chromadb
from chromadb.config import Settings

from backend.services.embedding_utils import get_single_embedding
from backend.services.gcs_loader import get_client

# Local persistent ChromaDB path
DB_PATH = os.path.join(os.getcwd(), "chroma_db")

# Initialize Chroma client (no telemetry)
client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(
        anonymized_telemetry=False,
    )
)

def get_collection():
    """
    Get or create the ChromaDB collection for transcript embeddings.
    IMPORTANT: embedding_function=None disables Chroma's default ONNX
    embedding model (384-dim) to avoid dimensional mismatch.
    """
    return client.get_or_create_collection(
        name="udemy_transcripts",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None  # <-- CRITICAL FIX
    )


def save_chunks(video_name: str, chunks: list, embeddings: list):
    """
    Store transcript text chunks + embeddings in ChromaDB.
    All embeddings must have dimension 1536 (OpenAI text-embedding-3-small).
    """
    collection = get_collection()

    ids = []
    metadatas = []
    documents = []

    for idx, chunk in enumerate(chunks):
        ids.append(f"{video_name}_chunk_{idx}")
        metadatas.append({
            "video": video_name,
            "chunk_index": idx
        })
        documents.append(chunk)

    # Validate embedding dimensions
    for emb in embeddings:
        if len(emb) != 1536:
            raise ValueError(f"Invalid embedding dimension {len(emb)} — expected 1536")

    collection.add(
        ids=ids,
        metadatas=metadatas,
        documents=documents,
        embeddings=embeddings
    )

    return True


def save_summary_to_gcs(bucket_name: str, video_name: str, summary: str):
    """
    Save summary text to GCS in summaries/ folder.
    """
    storage_client = get_client()
    bucket = storage_client.bucket(bucket_name)

    blob_name = f"summaries/{video_name.replace('.txt', '_summary.txt')}"
    blob = bucket.blob(blob_name)

    blob.upload_from_string(summary, content_type="text/plain")

    return blob_name