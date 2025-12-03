import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary(transcript_text: str) -> str:
    print("Generating summary... transcript length:", len(transcript_text))

    prompt = f"""
    Summarize the following lecture transcript into 8-10 concise sentences:

    ---
    {transcript_text}
    ---
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        timeout=30   # timeout to avoid hanging
    )

    summary = response.choices[0].message.content.strip()
    print("Summary generated. Length:", len(summary))
    return summary

def generate_summary_for_question(question: str) -> str:
    """
    Create notes/summary for user question.
    e.g. 'Make notes for video 3'
    """
    prompt = f"Make simple, short notes for: {question}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content