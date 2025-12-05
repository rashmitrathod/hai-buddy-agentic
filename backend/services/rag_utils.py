import os
from openai import OpenAI

from backend.services.vector_store_lance import query_chunks

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def rag_answer(query: str):
    """
    Simple RAG utility:
    1. Retrieve relevant transcript chunks using LanceDB
    2. Build context
    3. Generate answer from LLM
    """

    # 1. Retrieve chunks using LanceDB (internally performs embeddings)
    retrieved_chunks = query_chunks(query)

    if not retrieved_chunks:
        return "I don’t see this in the uploaded course transcripts."

    # 2. Build RAG context block
    context_text = "\n\n".join(retrieved_chunks)

    prompt = f"""
You are a helpful AI tutor.

Use ONLY the following transcript context to answer the question.
If the answer is not present in the transcript, say:
"I don’t see this in the uploaded course transcripts."

---------------------
Context:
{context_text}
---------------------

Question:
{query}

Answer clearly and concisely. Use bullet points if helpful.
"""

    # 3. Generate final answer using OpenAI LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    return response.choices[0].message.content