import chromadb
from chromadb.config import Settings
import os

from backend.services.embedding_utils import get_single_embedding
from backend.services.gcs_loader import get_client

# Cloud Run–safe: in-memory Chroma client
client = chromadb.Client(
    Settings(
        anonymized_telemetry=False,
    )
)

def get_collection():
    return client.get_or_create_collection(
        name="udemy_transcripts",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None
    )

def save_chunks(video_name: str, chunks: list, embeddings: list):
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
    storage_client = get_client()
    bucket = storage_client.bucket(bucket_name)

    blob_name = f"summaries/{video_name.replace('.txt', '_summary.txt')}"
    blob = bucket.blob(blob_name)

    blob.upload_from_string(summary, content_type="text/plain")
    return blob_name

def query_chunks(query_embedding, top_k: int = 5) -> list[str]:
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results.get("documents", [[]])[0]

def get_memory_collection():
    return client.get_or_create_collection(
        name="hai_memory",
        metadata={"hnsw:space": "cosine"}
    )