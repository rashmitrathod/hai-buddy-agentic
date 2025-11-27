# backend/services/tts.py

import uuid
from google.cloud import texttospeech
from backend.services.gcs_loader import upload_audio_bytes

def synthesize_text_to_gcs(text: str) -> str:
    """
    Convert text → speech → upload to GCS → return public URL.
    """

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # create file name
    filename = f"audio/{str(uuid.uuid4())}.mp3"

    # upload to GCS
    public_url = upload_audio_bytes(filename, response.audio_content)

    return public_url