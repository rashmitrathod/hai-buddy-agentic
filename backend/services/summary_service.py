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
        timeout=30   # <-- add timeout to avoid hanging
    )

    summary = response.choices[0].message.content.strip()
    print("Summary generated. Length:", len(summary))
    return summary