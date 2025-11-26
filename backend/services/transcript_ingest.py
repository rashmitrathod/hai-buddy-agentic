from google.cloud import storage
from backend.services.gcs_loader import load_transcript
import os

BUCKET_NAME = os.getenv("GCS_BUCKET")
TRANSCRIPT_FOLDER = "transcripts/"

def list_transcripts():
    """List all transcript files in the bucket"""
    client = storage.Client()
    blobs = client.list_blobs(BUCKET_NAME, prefix=TRANSCRIPT_FOLDER)
    return [blob.name for blob in blobs if blob.name.endswith(".txt")]

def load_all_transcripts():
    """Load all transcripts from GCS as a dict"""
    transcripts = {}
    for blob_name in list_transcripts():
        video_name = os.path.basename(blob_name)
        content = load_transcript(BUCKET_NAME, blob_name)
        transcripts[video_name] = content
    return transcripts