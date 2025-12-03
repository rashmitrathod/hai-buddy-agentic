from google.cloud import speech_v1 as speech
from google.cloud import storage
# from pydub import AudioSegment
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

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""

    transcript = response.results[0].alternatives[0].transcript
    return transcript