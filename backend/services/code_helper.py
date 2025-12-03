from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def answer_code_question(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a python and cloud expert. Explain clearly and concisely."},
            {"role": "user", "content": question}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content