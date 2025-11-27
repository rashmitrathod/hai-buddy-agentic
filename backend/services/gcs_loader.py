import os
import uuid
from datetime import timedelta
from google.cloud import storage
from dotenv import load_dotenv


def get_client():
    return storage.Client()

def list_transcripts(bucket_name: str, prefix: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = client.list_blobs(bucket, prefix=prefix)
    # Only return actual files (exclude folders)
    return [blob for blob in blobs if not blob.name.endswith("/")]

def load_transcript(bucket_name: str, blob_name: str) -> str:
    print(f'Inside load_transcript, bucket_name:{bucket_name}, blob_name:{blob_name}')
    if not bucket_name:
        raise ValueError("Bucket name is missing. Check .env GCS_BUCKET_NAME.")

    client = get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    print(f'blob:{blob}, blob_size:{blob.size}')
    transcript = blob.download_as_text()
    print(f'transcript:{transcript}')

    return transcript


load_dotenv(override=True)
BUCKET_NAME = os.getenv("GCS_BUCKET")

# backend/services/gcs_audio.py
import os
import uuid
from datetime import timedelta
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv(override=True)

BUCKET_NAME = os.getenv("GCS_BUCKET")

def upload_audio_bytes(filename: str, audio_bytes: bytes) -> str:
    """
    Upload audio bytes to GCS bucket and return a signed URL.
    If filename is None or empty, generate a UUID-based filename.
    """
    if not BUCKET_NAME:
        raise ValueError("GCS_BUCKET not set in environment")

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Use provided filename or generate one
    if not filename:
        filename = f"audio/{uuid.uuid4()}.mp3"
    else:
        # Ensure it's under 'audio/' folder
        if not filename.startswith("audio/"):
            filename = f"audio/{filename}"

    blob = bucket.blob(filename)
    
    # Upload raw audio bytes
    blob.upload_from_string(audio_bytes, content_type="audio/mpeg")

    # Generate a signed URL valid for 1 hour
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET"
    )

    return url