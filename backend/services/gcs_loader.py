import os
from google.cloud import storage

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
