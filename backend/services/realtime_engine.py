import json
import base64
from typing import AsyncGenerator

from openai import AsyncOpenAI

from backend.services.rag_engine import query_chunks, generate_llm_answer
from backend.services.memory_store import write_memory
from backend.services.language_utils import is_hinglish
from backend.services.tts import synthesize_text_to_gcs


# Initialize OpenAI realtime client
client = AsyncOpenAI()

async def process_realtime_message(event: dict) -> AsyncGenerator[dict, None]:
    """
    Called every time the frontend sends a realtime event.
    Handles:
      - STT transcript events
      - audio chunks (ignored here; STT API handles that)
      - response creation
    """

    # 1. Handle transcription events from OpenAI
    if event.get("type") == "response.output_text.delta":
        text = event.get("delta", "")
        if text.strip():
            yield {"type": "transcript.partial", "text": text}

    if event.get("type") == "response.output_text.done":
        full_text = event.get("text", "")

        # 2. Store to memory
        update_memory("user_last_message", full_text)

        # 3. Determine language (English / Hinglish)
        hinglish = is_hinglish(full_text)

        # 4. Retrieve RAG context
        context = query_chunks(full_text)

        # 5. Generate final answer (CrewAI logic happens in generate_llm_answer)
        final_answer = generate_llm_answer(full_text, context)

        # 6. Convert answer to TTS (GCS URL)
        audio_url = synthesize_text_to_gcs(final_answer)

        # 7. Send text output
        yield {
            "type": "final.text",
            "answer": final_answer
        }

        # 8. Send audio output for the player
        yield {
            "type": "final.audio",
            "audio_url": audio_url
        }