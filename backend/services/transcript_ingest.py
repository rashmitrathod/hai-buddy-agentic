from google.cloud import storage
from backend.services.gcs_loader import load_transcript
import os

BUCKET_NAME = os.getenv("GCS_BUCKET")
TRANSCRIPT_FOLDER = "transcripts/"

def list_transcripts(bucket_name: str, prefix: str):
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = client.list_blobs(bucket, prefix=prefix)
    # Filter out directories/folders
    return [blob for blob in blobs if blob.name.endswith(".txt")]

def load_all_transcripts():
    """Load all transcripts from GCS as a dict"""
    print('Inside load_all_transcripts')
    transcripts = {}
    for blob_name in list_transcripts():
        video_name = os.path.basename(blob_name)
        content = load_transcript(BUCKET_NAME, blob_name)
        transcripts[video_name] = content
    print(f'transcripts: {transcripts}')
    return transcripts