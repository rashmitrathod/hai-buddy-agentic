from fastapi import APIRouter
from backend.services.gcs_loader import load_transcript
import os

router = APIRouter()

# Read bucket name from .env automatically
BUCKET_NAME = os.getenv("GCS_BUCKET")

@router.get("/transcript/{video_name}")
def get_transcript(video_name: str):
    """
    Example: video_name = video1_transcript.txt
    """
    if not BUCKET_NAME:
        return {"error": "Cannot determine path without bucket name."}
    try:
        content = load_transcript(BUCKET_NAME, f"transcripts/{video_name}")
        return {"video_name": video_name, "content": content[:1000]}  # first 1000 chars
    except Exception as e:
        return {"error": str(e)}