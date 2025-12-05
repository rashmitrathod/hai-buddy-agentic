import os
from google.cloud import storage
import numpy as np

from backend.services.text_chunker import chunk_text
from backend.services.embedding_utils import get_single_embedding
from backend.services.vector_store_lance import insert_transcript_chunk, get_transcript_table
from backend.services.embedding_normalizer import normalize_embedding


BUCKET_NAME = os.getenv("GCS_BUCKET")
TRANSCRIPT_PREFIX = "transcripts/"  # folder in bucket


def list_transcripts():
    """Return list of transcript blob objects under gs://<BUCKET>/transcripts/"""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=TRANSCRIPT_PREFIX))
    return [b for b in blobs if b.name.endswith(".txt")]


def load_and_index_transcripts(max_tokens: int = 300, overlap: int = 50):
    """
    1) Scan GCS transcripts folder
    2) Download each transcript
    3) Token-chunk using chunk_text(...)
    4) Embed each chunk (get_single_embedding)
    5) Insert into LanceDB via insert_transcript_chunk()

    Returns a dict with counts for easy /setup responses.
    """
    blobs = list_transcripts()
    total_files = len(blobs)
    if total_files == 0:
        return {"status": "no transcripts found", "files_indexed": 0, "chunks_indexed": 0}

    # ensure table exists (creates if missing)
    _ = get_transcript_table()

    total_chunks = 0
    for blob in blobs:
        filename = os.path.basename(blob.name)
        video_id = filename.replace(".txt", "")
        print(f"Processing {blob.name} -> video_id={video_id}")

        # download text robustly
        try:
            text = blob.download_as_text(encoding="utf-8")
        except Exception:
            text = blob.download_as_bytes().decode("utf-8", errors="ignore")

        # chunk (token-based chunker)
        chunks = chunk_text(text, max_tokens=max_tokens, overlap=overlap)
        print(f"  Created {len(chunks)} chunks for {video_id}")

        for idx, chunk in enumerate(chunks):
            emb = get_single_embedding(chunk)
            # normalize embedding
            emb_list = normalize_embedding(emb)


            insert_transcript_chunk(video=video_id, chunk_index=idx, chunk=chunk, embedding=emb_list)

        total_chunks += len(chunks)
        print(f"  Indexed {len(chunks)} chunks for {video_id}")

    return {"status": "ok", "files_indexed": total_files, "chunks_indexed": total_chunks}