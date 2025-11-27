# backend/route/embeddings.py
import os
from fastapi import APIRouter
from backend.services.gcs_loader import list_transcripts, load_transcript
from backend.services.chunk_utils import stream_chunks
from backend.services.embedding_utils import get_embedding
from backend.services.vector_store import save_chunks

router = APIRouter()

@router.post("/generate_embeddings")
def generate_embeddings():
    bucket = os.getenv("GCS_BUCKET")
    prefix = "summaries/"

    blobs = list_transcripts(bucket, prefix)

    for blob in blobs:
        content = load_transcript(bucket, blob.name)
        chunks = list(stream_chunks(content))
        if not chunks:
            continue

        embeddings = get_embedding(chunks)
        save_chunks(blob.name, chunks, embeddings)

    return {"status": "embeddings saved to ChromaDB"}