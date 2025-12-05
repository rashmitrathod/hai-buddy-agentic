import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary(transcript_text: str) -> str:
    prompt = f"""
    Summarize the following lecture transcript into 8–10 very concise sentences:

    ---
    {transcript_text}
    ---
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You summarize course transcripts clearly and concisely."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300
    )

    return response.choices[0].message.content.strip()


def generate_summary_for_question(question: str) -> str:
    """
    Used when intent classifier detects: notes / summary request
    e.g. "Make notes for video 3"
    """

    prompt = f"""
    Create short, simple notes for the following request:

    "{question}"

    The notes must be concise (4–6 bullets) and easy to understand.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate concise study notes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )

    return response.choices[0].message.content.strip()