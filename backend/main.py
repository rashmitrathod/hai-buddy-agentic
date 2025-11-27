from fastapi import FastAPI
from backend.api.transcript_api import router as transcript_router
from dotenv import load_dotenv
from backend.services.gcs_loader import load_transcript, list_transcripts
from backend.services.chunk_utils import stream_chunks
from backend.services.embedding_utils import get_embedding

from backend.services.vector_store import save_chunks
import backend.services.embedding_utils as embedding_utils
from backend.services.chunk_utils import stream_chunks

from backend.services import vector_store

from backend.services.rag_utils import rag_answer

from backend.route.summaries import router as summaries_router

import os

# $env:GOOGLE_APPLICATION_CREDENTIALS="C:\personal-rashmit\personal\technical_study_learning\Agentic_AI\POC\hai-buddy-agentic\hai-buddy-agentic-sa-key.json"

# Load .env file automatically
load_dotenv(override=True)

# Verify env variables
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("GCS_BUCKET:", os.getenv("GCS_BUCKET"))

app = FastAPI()
app.include_router(transcript_router)

app.include_router(summaries_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/test_load")
def test_load():
    data = load_all_transcripts()
    return {"videos_loaded": list(data.keys())}

@app.get("/test_chunks")
def test_chunks():
    bucket = os.getenv("GCS_BUCKET")
    prefix = "transcripts/"

    print("DEBUG BUCKET:", bucket)
    blobs = list_transcripts(bucket, prefix)

    results = {}

    for blob in blobs:
        content = load_transcript(bucket, blob.name)

        sample_embeddings = []
        count = 0

        # Only generate embeddings for first 3 chunks
        for chunk in stream_chunks(content):
            emb = get_embedding(chunk)
            sample_embeddings.append(len(emb))
            count += 1
            if count == 3:
                break

        results[blob.name] = sample_embeddings

    return {
        "status": "embedding test completed",
        "embedding_vector_lengths": results
    }


@app.get("/test_embed")
def test_embed():
    bucket = os.getenv("GCS_BUCKET")
    prefix = "transcripts/"

    blobs = list_transcripts(bucket, prefix)

    for blob in blobs:
        print("Found file:", blob.name)
        content = load_transcript(bucket, blob.name)
        print(f"DEBUG: {blob.name} content length:", len(content))
        chunks = list(stream_chunks(content))
        print(f"DEBUG: {blob.name} -> {len(chunks)} chunks generated")

        embeddings = embedding_utils.get_embedding(chunks)
        vector_store.save_chunks(blob.name, chunks, embeddings)

    return {"status": "embedding saved to ChromaDB"}




@app.post("/ask")
def ask_question(payload: dict):
    question = payload.get("question", "").strip()

    if not question:
        return {"error": "Question cannot be empty"}

    answer = rag_answer(question)

    return {
        "question": question,
        "answer": answer
    }


@app.get("/test_summary")
def test_summary():
    from backend.services.summary_service import generate_summary
    text = "This is a test transcript. It teaches how to create AI agents using tools..."
    return {"summary": generate_summary(text)}
