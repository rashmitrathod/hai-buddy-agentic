import os
import chromadb
from chromadb.config import Settings

from backend.services.embedding_utils import get_single_embedding

# Persistent database directory
DB_PATH = os.path.join(os.getcwd(), "chroma_db")

# ---- New Chroma client syntax ----
client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(
        anonymized_telemetry=False
    )
)

def get_collection():
    return client.get_or_create_collection(
        name="udemy_transcripts",
        metadata={"hnsw:space": "cosine"}
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

    collection.add(
        ids=ids,
        metadatas=metadatas,
        documents=documents,
        embeddings=embeddings
    )

    return True

from backend.services.gcs_loader import get_client

def save_summary_to_gcs(bucket_name: str, video_name: str, summary: str):
    client = get_client()
    bucket = client.bucket(bucket_name)
    blob_name = f"summaries/{video_name.replace('.txt','_summary.txt')}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(summary, content_type="text/plain")
    return blob_name