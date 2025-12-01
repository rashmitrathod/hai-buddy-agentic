from google.cloud import speech_v1 as speech
from google.cloud import storage
from pydub import AudioSegment
import uuid
import os
import io

def transcribe_audio(audio_bytes: bytes) -> str:
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-IN",
        enable_automatic_punctuation=True
    )

    # config = {
    # "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
    # "sample_rate_hertz": 44100,
    # "language_code": "en-IN",   # Indian English -> better for your accent
    # "enable_automatic_punctuation": True,
    # "use_enhanced": True,
    # "model": "default",         # or "latest_long" → better accuracy
    # "speech_contexts": [
    #     {"phrases": ["CrewAI", "Agentic AI", "HAI Buddy", "AI agent", "agentic"], "boost": 20}
    # ]
    # }


    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""

    transcript = response.results[0].alternatives[0].transcript
    return transcript


# def transcribe_audio(file_bytes: bytes):

#     # ---- STEP 1: Convert WEBM → WAV (LINEAR16) ----
#     audio = AudioSegment.from_file(io.BytesIO(file_bytes), format="webm")
#     wav_io = io.BytesIO()
#     audio.set_frame_rate(44100).set_channels(1).set_sample_width(2).export(wav_io, format="wav")
#     wav_bytes = wav_io.getvalue()

#     # ---- STEP 2: Send WAV to Google STT ----
#     client = speech.SpeechClient()

#     audio_config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=44100,
#         language_code="en-IN",
#         enable_automatic_punctuation=True,
#         use_enhanced=True,
#         model="latest_long",
#         speech_contexts=[
#             speech.SpeechContext(
#                 phrases=["CrewAI", "Agentic AI", "HAI Buddy", "AI agent"],
#                 boost=20
#             )
#         ]
#     )

#     audio_data = speech.RecognitionAudio(content=wav_bytes)

#     response = client.recognize(config=audio_config, audio=audio_data)

#     if not response.results:
#         return ""

#     return response.results[0].alternatives[0].transcript