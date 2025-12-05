import os
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import APIRouter, UploadFile, File
from google.cloud import speech

from backend.api.transcript_api import router as transcript_router
from dotenv import load_dotenv
from backend.services.gcs_loader import load_transcript, list_transcripts
from backend.services.chunk_utils import stream_chunks
from backend.services.embedding_utils import get_embedding

# from backend.services.vector_store_lance import save_chunks
import backend.services.embedding_utils as embedding_utils
from backend.services.chunk_utils import stream_chunks

from backend.services import vector_store_lance

from backend.services.rag_utils import rag_answer

from backend.route.summaries import router as summaries_router

from backend.services.stt_service import transcribe_audio

import uuid
from fastapi import FastAPI, UploadFile, File
from backend.services.rag_pipeline import answer_question
from backend.services.tts import synthesize_text_to_gcs

from backend.services.intent_classifier import classify_intent
from backend.services.router import route_question

from backend.services.sse_chat import router as sse_router
from backend.route.setup_loader import router as setup_router



# Load .env file automatically
load_dotenv(override=True)

# Verify env variables
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
print("GCS_BUCKET:", os.getenv("GCS_BUCKET"))

app = FastAPI()

app.include_router(transcript_router)
app.include_router(summaries_router)
app.include_router(sse_router)
app.include_router(setup_router)


@app.get("/health")
def health_check():
    print('Inside /health route')
    return {"status": "ok"}

@app.get("/talk")
def talk_page():
    return FileResponse("frontend/index.html")



# @app.get("/test_load")
# def test_load():
#     data = load_all_transcripts()
#     return {"videos_loaded": list(data.keys())}

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


# @app.get("/test_embed")
# def test_embed():
#     bucket = os.getenv("GCS_BUCKET")
#     prefix = "transcripts/"

#     blobs = list_transcripts(bucket, prefix)

#     for blob in blobs:
#         print("Found file:", blob.name)
#         content = load_transcript(bucket, blob.name)
#         print(f"DEBUG: {blob.name} content length:", len(content))
#         chunks = list(stream_chunks(content))
#         print(f"DEBUG: {blob.name} -> {len(chunks)} chunks generated")

#         embeddings = embedding_utils.get_embedding(chunks)
#         vector_store_lance.save_chunks(blob.name, chunks, embeddings)

#     return {"status": "embedding saved to ChromaDB"}


from backend.services.rag_engine import (
    retrieve_relevant_chunks,
    build_context,
    generate_llm_answer
)

class AskRequest(BaseModel):
    question: str

# from fastapi import Request
# from backend.services.crew.orchestrator_agent import CrewOrchestrator
# from backend.services.tts import synthesize_text_to_gcs

# @app.post("/ask")
# async def ask_endpoint(request: Request):
  
#     body = await request.json()
#     question = body.get("question")

#     session_id = request.get("session_id", "default_session")
#     orchestrator = CrewOrchestrator(session_id=session_id)

#     if not question:
#         return {"error": "No question provided"}

#     # Run CrewAI multi-agent pipeline
#     orchestrator = CrewOrchestrator()
#     # final_answer = orchestrator.run(question)
#     # final_answer, intent = route_question(question)
#     final_answer = orchestrator.run(question)

#     # Generate speech URL
#     audio_url = synthesize_text_to_gcs(final_answer)

#     return {
#         "question": question,
#         "answer": final_answer,
#         "audio_url": audio_url
#     }


# @app.get("/test_summary")
# def test_summary():
#     from backend.services.summary_service import generate_summary
#     text = "This is a test transcript. It teaches how to create AI agents using tools..."
#     return {"summary": generate_summary(text)}


# @app.post("/stt")
# async def speech_to_text(file: UploadFile = File(...)):
#     audio_bytes = await file.read()

#     transcript = transcribe_audio(audio_bytes)

#     return {
#         "transcript": transcript
#     }

####

router = APIRouter()
speech_client = speech.SpeechClient()

@router.post("/stt")
async def stt_route(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,  # Chrome usually records at 48000 Hz
        language_code="en-US",
        audio_channel_count=1,
        enable_automatic_punctuation=True
    )

    response = speech_client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    return {"transcript": transcript}

app.include_router(router)
####

@app.post("/test_intent")
def test_intent(req: dict):
    question = req.get("question")
    intent = classify_intent(question)
    return {"question": question, "intent": intent}


from backend.services.crew.orchestrator_agent import CrewOrchestrator
orchestrator = CrewOrchestrator()

@app.post("/ask_new")
def ask_new(req: dict):
    print(f"/ask_new has invoked")
    question = req.get("question")
    print(f"question: {question}")
    answer = orchestrator.run(question)
    return {"question": question, "answer": answer}



# =========================
#  ADD THIS TO main.py
# =========================
from fastapi import UploadFile, File
from google.cloud import storage
import uuid
from openai import OpenAI
import os
import base64

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BUCKET_NAME = os.getenv("GCS_BUCKET")


@app.post("/tts")
async def text_to_speech(req: dict):
    """
    Convert text → MP3 using OpenAI TTS.
    Store MP3 in GCS and return public URL.
    """
    text = req.get("text", "").strip()
    session_id = req.get("session_id", "default")

    if not text:
        return {"error": "text is required"}

    # ---- 1) Call OpenAI TTS ----
    audio_response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        format="mp3"
    )

    audio_bytes = audio_response.read()

    # ---- 2) Upload to GCS ----
    filename = f"tts/{session_id}_{uuid.uuid4()}.mp3"
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    blob.upload_from_string(audio_bytes, content_type="audio/mpeg")

    # Make the file public
    blob.make_public()

    return {"audio_url": blob.public_url}