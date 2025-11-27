from google.cloud import speech_v1 as speech
from google.cloud import storage
import uuid
import os


def transcribe_audio(audio_bytes: bytes) -> str:
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-IN",
        enable_automatic_punctuation=True
    )

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""

    transcript = response.results[0].alternatives[0].transcript
    return transcript