from openai import OpenAI
import os

from backend.services.embedding_utils import get_embedding
from backend.services.vector_store import get_collection

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def rag_answer(query: str):
    # 1. Embed the question
    query_embedding = get_embedding([query])[0]

    # 2. Search similar chunks in ChromaDB
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    retrieved_chunks = results.get("documents", [[]])[0]

    if not retrieved_chunks:
        return "No relevant context found in transcripts."

    # 3. Build prompt
    context_text = "\n\n".join(retrieved_chunks)

    prompt = f"""
You are a helpful AI tutor.

Use ONLY the following transcript context to answer the question.
If the answer is not present in the transcript, say:
"I don’t see this in the uploaded course transcripts."

Context:
{context_text}

Question:
{query}

Answer in clear bullet points where possible.
"""

    # 4. Call LLM for final answer
    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content