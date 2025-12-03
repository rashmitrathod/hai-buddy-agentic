import json
from backend.services.intent_classifier import classify_intent
from backend.services.language_detector import is_hinglish
from backend.services.vector_store import query_chunks
from backend.services.memory_service import recall_memory, write_memory
from backend.services.crew.orchestrator_agent import orchestrator
from backend.services.persona import build_persona_prompt

from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def process_realtime_message(payload):
    """
    This function receives a browser payload (text-only for now),
    executes the full HAI Buddy pipeline,
    and yields events for the WebSocket to send back.

    Yields:
        OpenAI Realtime events (dicts)
    """

    if payload["type"] != "user_message":
        return

    user_text = payload["text"]

    # ---------------------------------------
    # 1. Memory Recall
    # ---------------------------------------
    mem_context = recall_memory(user_text)

    # ---------------------------------------
    # 2. Intent Classification
    # ---------------------------------------
    intent = classify_intent(user_text)

    # ---------------------------------------
    # 3. Hinglish Detection
    # ---------------------------------------
    hinglish = is_hinglish(user_text)

    # ---------------------------------------
    # 4. RAG Retrieval
    # ---------------------------------------
    context_chunks = query_chunks(user_text)

    merged_context = "\n".join(
        [m["document"] for m in context_chunks]
    )

    # ---------------------------------------
    # 5. Multi-Agent CrewAI Reasoning
    # ---------------------------------------
    try:
        agent_reasoning = orchestrator.run(user_text)
    except Exception as ex:
        agent_reasoning = f"(CrewAI error: {ex})"

    # ---------------------------------------
    # 6. Construct Persona Prompt
    # ---------------------------------------
    persona_prompt = build_persona_prompt(
        query=user_text,
        context=merged_context,
        memory=mem_context,
        agent_result=agent_reasoning,
        hinglish=hinglish,
    )

    # ---------------------------------------
    # 7. Call OpenAI Realtime model for final answer
    # ---------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": persona_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=250
    )

    final_text = response.choices[0].message.content

    # ---------------------------------------
    # 8. Save final answer into memory
    # ---------------------------------------
    write_memory(user_text, final_text)

    # ---------------------------------------
    # 9. Yield back to WebSocket (OpenAI Realtime format)
    # ---------------------------------------
    yield {
        "type": "response.output_text.done",
        "text": final_text
    }

    # Audio will be handled automatically by the realtime WS