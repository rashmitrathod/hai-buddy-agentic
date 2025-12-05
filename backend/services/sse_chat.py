import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# IMPORT THE GLOBAL SHARED ORCHESTRATOR
from backend.services.crew.orchestrator_agent import CrewOrchestrator

# Reuse the same global orchestrator used by /ask_new
global_orchestrator = CrewOrchestrator()

router = APIRouter()

@router.get("/stream/chat/{session_id}")
async def stream_chat(session_id: str, question: str):

    async def event_generator():

        # 1. Handshake
        yield "data: " + json.dumps({
            "type": "connection",
            "session": session_id
        }) + "\n\n"

        # 2. Typing indicator
        yield "data: " + json.dumps({
            "type": "assistant_typing",
            "message": "Thinking..."
        }) + "\n\n"

        try:
            # 3. RUN THE SAME ORCHESTRATOR AS /ask_new
            answer_text = await asyncio.to_thread(global_orchestrator.run, question)

            yield "data: " + json.dumps({
                "type": "assistant_message",
                "text": answer_text
            }) + "\n\n"

        except Exception as exc:
            yield "data: " + json.dumps({
                "type": "error",
                "message": f"Server error: {str(exc)}"
            }) + "\n\n"

        # 4. End of SSE stream
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")