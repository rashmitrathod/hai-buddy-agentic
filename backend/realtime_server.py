# backend/realtime_server.py
import os
import json
import asyncio
import websockets
from fastapi import WebSocket

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime"  # adapt model if needed

# hook to your existing orchestrator
from backend.services.crew.orchestrator_agent import CrewOrchestrator  # returns final answer text

# async def handle_realtime_websocket(client_ws: WebSocket):
#     await client_ws.accept()

#     # Connect to OpenAI Realtime WS
#     async with websockets.connect(
#         OPENAI_WS_URL,
#         extra_headers={
#             "Authorization": f"Bearer {OPENAI_API_KEY}",
#             "OpenAI-Beta": "realtime=v1"
#         },
#         max_size=None
#     ) as openai_ws:

#         # tasks
#         async def client_to_openai():
#             """
#             Read messages from browser and forward/translate to OpenAI WS.
#             Expected browser messages: JSON strings like:
#               { type: "input_audio_buffer.append", audio: "<base64>" }
#               { type: "input_audio_buffer.commit" }
#             """
#             while True:
#                 try:
#                     m = await client_ws.receive_text()
#                 except Exception:
#                     break

#                 try:
#                     data = json.loads(m)
#                 except Exception:
#                     # ignore non-json
#                     continue

#                 # If browser sends audio chunk base64 -> forward as-is to OpenAI
#                 if data.get("type") == "input_audio_buffer.append":
#                     # OpenAI expects raw bytes in array form OR base64 depending on client;
#                     # Realtime WS accepts JSON with "type":"input_audio_buffer.append" and "audio":"<base64>"
#                     await openai_ws.send(json.dumps({
#                         "type": "input_audio_buffer.append",
#                         "audio": data.get("audio")
#                     }))

#                 elif data.get("type") == "input_audio_buffer.commit":
#                     # commit so OpenAI processes the audio and emits transcript events
#                     await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

#                 else:
#                     # Forward any other event directly (safe)
#                     await openai_ws.send(json.dumps(data))

#         async def openai_to_client():
#             """
#             Forward OpenAI events to browser, but intercept final transcript events to run
#             the orchestrator and request a spoken response from OpenAI.
#             """
#             while True:
#                 try:
#                     msg = await openai_ws.recv()
#                 except Exception:
#                     break

#                 try:
#                     obj = json.loads(msg)
#                 except Exception:
#                     # If not JSON, forward raw
#                     await client_ws.send_text(msg)
#                     continue

#                 # Forward transcript deltas immediately so UI can show partial captions
#                 if obj.get("type") in ("response.output_text.delta", "response.output_text.done"):
#                     # Forward to client
#                     await client_ws.send_text(json.dumps(obj))

#                 # When OpenAI emits final completed transcript
#                 if obj.get("type") == "response.output_text.done":
#                     final_text = obj.get("text", "").strip()
#                     if final_text:
#                         # 1) call orchestrator (your HAI Buddy pipeline)
#                         try:
#                             # orchestrator.run should be synchronous; call in thread if blocking
#                             loop = asyncio.get_running_loop()
#                             final_answer = await loop.run_in_executor(None, CrewOrchestrator.run, final_text)
#                         except Exception as e:
#                             final_answer = f"Sorry, an internal error while answering: {e}"

#                         # 2) Ask OpenAI to synthesize spoken response for final_answer
#                         # Send a create response with instructions = final_answer
#                         create_req = {
#                             "type": "response.create",
#                             "response": {
#                                 # instructions will be spoken by OpenAI, and can optionally also return text blocks
#                                 "instructions": final_answer,
#                                 # optionally request voice/preset if supported, example:
#                                 # "modalities": ["audio", "text"]
#                             }
#                         }
#                         await openai_ws.send(json.dumps(create_req))

#                 # Forward OpenAI audio deltas to the browser so UI can play audio
#                 if obj.get("type") == "response.output_audio.delta":
#                     # obj['delta'] is base64 chunk, forward it
#                     await client_ws.send_text(json.dumps(obj))

#                 # Forward other useful events as-is (safety, errors, etc.)
#                 if obj.get("type") not in ("response.output_text.delta", "response.output_text.done", "response.output_audio.delta"):
#                     await client_ws.send_text(json.dumps(obj))

#         # run both concurrently
#         t1 = asyncio.create_task(client_to_openai())
#         t2 = asyncio.create_task(openai_to_client())

#         await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)

#         # cleanup
#         t1.cancel()
#         t2.cancel()