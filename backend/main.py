from fastapi import FastAPI
from backend.api.transcript_api import router as transcript_router
from dotenv import load_dotenv
import os

# Load .env file automatically
load_dotenv()

# Verify env variables
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("GCS_BUCKET:", os.getenv("GCS_BUCKET"))

app = FastAPI()
app.include_router(transcript_router)


from backend.services.transcript_ingest import load_all_transcripts

@app.get("/test_load")
def test_load():
    data = load_all_transcripts()
    return {"videos_loaded": list(data.keys())}


from backend.services.transcript_ingest import load_all_transcripts
from backend.services.chunk_utils import chunk_text

@app.get("/test_chunks")
def test_chunks():
    transcripts = load_all_transcripts()
    chunks_per_video = {}
    for video, content in transcripts.items():
        chunks_per_video[video] = chunk_text(content)
    return {video: len(chunks) for video, chunks in chunks_per_video.items()}
