import os
from dotenv import load_dotenv
from openai import OpenAI

from backend.services.vector_store_lance import query_chunks
from backend.services.embedding_utils import get_single_embedding
from backend.services.language_utils import is_hinglish

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def retrieve_relevant_chunks(query: str, top_k: int = 3):
    """
    LanceDB-compatible retrieval for backwards compatibility.
    Returns:
      documents: list[str]
      metadatas: None (LanceDB does not store metadata by default)
    """
    try:
        documents = query_chunks(query)[:top_k]
        return documents, None
    except Exception:
        return [], None


# ------------------------------------------------------------
# Build transcript context
# ------------------------------------------------------------
def build_context(chunks: list) -> str:
    return "\n\n".join(chunks)


# ------------------------------------------------------------
# Generate answer with persona + Hinglish rules
# ------------------------------------------------------------
def generate_llm_answer(query: str, context: str):
    system_prompt = f"""
You are HAI Buddy — a friendly male buddy who explains concepts in a casual, simple, and helpful way.
Keep responses short (2–3 sentences), warm, conversational, and never formal or academic.

Rules:
- If user speaks Hinglish → reply ONLY in Hinglish (70% Hindi, 30% English).
- If user speaks English → reply ONLY in English.
- Match user tone exactly.
- No emojis or “buddy/friend/haha”.

Use ONLY this transcript context:

=====================
{context}
=====================
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    if is_hinglish(query):
        messages.append({
            "role": "system",
            "content": (
                "IMPORTANT: User is speaking Hinglish. Reply ONLY in Hinglish "
                "in a natural desi tone."
            )
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300
    )

    return response.choices[0].message.content


# ------------------------------------------------------------
# Main RAG pipeline
# ------------------------------------------------------------
def answer_with_rag(question: str) -> str:
    """
    1. Retrieve relevant transcript chunks using LanceDB
    2. Build RAG context
    3. Generate final answer
    """

    # LanceDB handles embedding internally → pass raw question text
    chunks = query_chunks(question)

    if not chunks:
        return "Sorry, I could not find relevant information in your course transcripts."

    context = build_context(chunks)

    # Final LLM response
    answer = generate_llm_answer(question, context)
    return answer