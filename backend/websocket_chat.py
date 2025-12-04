# backend/websocket_chat.py
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi import status
from typing import Dict

from backend.services.rag_engine import answer_with_rag  # use existing function OR call your /ask endpoint logic
# OR, if you have a function that handles ask including audio generation, import that.
# from backend.services.ask_service import ask_question

router = APIRouter()

# Simple connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_json(self, client_id: str, data: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json(data)

manager = ConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    session_id — use to bind conversation memory. Frontend should create a session_id once and reuse.
    Protocol (JSON):
    - client -> { "type": "user_message", "text": "Hello" }
    - server -> { "type": "assistant_message", "text": "...", "audio_url": "<optional>" }
    - server -> { "type": "error", "message": "..." }
    """
    client_id = session_id
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                obj = json.loads(data)
            except Exception as e:
                await manager.send_json(client_id, {"type": "error", "message": "invalid json"})
                continue

            if obj.get("type") == "user_message":
                user_text = obj.get("text", "").strip()
                if not user_text:
                    await manager.send_json(client_id, {"type": "error", "message": "empty message"})
                    continue

                # Optional: echo back a "thinking" event
                await manager.send_json(client_id, {"type": "assistant_typing", "message": "Thinking..."})

                # ---- Use your existing ask pipeline here ----
                # If you already have an endpoint /ask that returns {"answer":..., "audio_url":...},
                # you can call it programmatically. Here we call a function answer_with_rag for example.
                try:
                    # If your ask flow requires session_id, pass it; adapt as necessary.
                    # If answer_with_rag only takes a question and returns text, use that.
                    # If you have a unified 'ask' function that returns answer+audio, call that instead.
                    # answer_text = answer_with_rag(user_text)
                    answer_text = await asyncio.to_thread(answer_with_rag, user_text)
                    # If your ask returns only text, audio may be added later by /tts
                    # Let’s attempt to fetch audio_url by calling /tts endpoint only when needed.
                    audio_url = None
                    # Optional: if you have synchronous tts endpoint:
                    # import requests
                    # tts_resp = requests.post(f"http://localhost:8899/tts", json={"text": answer_text, "session_id": session_id})
                    # if tts_resp.status_code == 200:
                    #     audio_url = tts_resp.json().get("audio_url")

                    # send assistant message back
                    await manager.send_json(client_id, {"type": "assistant_message", "text": answer_text, "audio_url": audio_url})

                except Exception as exc:
                    await manager.send_json(client_id, {"type": "error", "message": f"server error: {str(exc)}"})
            else:
                await manager.send_json(client_id, {"type": "error", "message": "unknown message type"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
