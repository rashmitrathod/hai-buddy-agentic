# backend/routes/summaries.py

import os
from fastapi import APIRouter
from backend.services.gcs_loader import load_transcript
from backend.services.summary_service import generate_summary
from backend.services.gcs_loader import get_client

router = APIRouter()

@router.post("/generate_summaries")
def generate_summaries():
    transcripts_dir = "transcripts/"
    bucket_name = os.getenv("GCS_BUCKET")

    if not bucket_name:
        return {"error": "GCS_BUCKET_NAME missing in .env"}

    # List all transcript files
    client = get_client()
    bucket = client.bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=transcripts_dir)

    summary_results = {}

    for blob in blobs:
        if blob.name.endswith(".txt"):

            transcript_text = load_transcript(bucket_name, blob.name)
            summary = generate_summary(transcript_text)

            save_summary_to_gcs(bucket_name, blob.name, summary)
            summary_results[blob.name] = "summary saved"

    return {"status": "summaries generated", "details": summary_results}


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