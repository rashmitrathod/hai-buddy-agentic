from backend.services.vector_store import get_collection
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def retrieve_relevant_chunks(query: str, top_k: int = 3):
#     """
#     Fetch the most relevant transcript chunks from ChromaDB.
#     """
#     collection = get_collection()

#     results = collection.query(
#         query_texts=[query],
#         n_results=top_k
#     )

#     documents = results.get("documents", [[]])[0]
#     metadatas = results.get("metadatas", [[]])[0]

#     return documents, metadatas

def retrieve_relevant_chunks(query: str, top_k: int = 3):
    """
    Fetch relevant transcript chunks from ChromaDB.
    IMPORTANT: We MUST disable Chroma's internal embedding function
    DURING QUERY TIME — otherwise Chroma uses MiniLM 384-dim.
    """

    collection = get_collection()

    # ---- FIX: compute embedding manually with OpenAI ----
    from backend.services.embedding_utils import get_single_embedding
    query_emb = get_single_embedding(query)

    results = collection.query(
        query_embeddings=[query_emb],   # <- use manual embedding
        n_results=top_k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    return documents, metadatas


def build_context(chunks: list) -> str:
    """
    Build a single context block from retrieved chunks.
    """
    context_text = "\n\n".join(chunks)
    return f"Relevant Course Transcript Chunks:\n\n{context_text}"


def generate_llm_answer(query: str, context: str) -> str:
    """
    Generate a grounded AI response using retrieved context.
    """

    system_prompt = f"""
You are **HAI Buddy** — a friendly, informal, and supportive study partner.
You explain things the way a smart friend would, not like a textbook.

Your communication style:
- Use simple, everyday language
- Keep answers short (2–3 sentences)
- Speak casually and warmly
- Use small examples when helpful
- Avoid academic or formal tone
- Prefer “Imagine…” / “Think of it like…” to explain concepts
- Never overload with details
- Do NOT use emojis, emoticons, or words like “smile”, “haha”, “buddy”, “friend”.
- Do NOT add encouragement phrases unless asked.
- Avoid extra fluff.
- Do NOT use emojis, emoticons, or words like “smile”, “buddy”, “friend”, etc.
Keep tone friendly but without emojis or commands.

You ONLY use the transcript context below to answer.

=====================
Transcript Context:
{context}
=====================

Now answer the user’s question in a friendly buddy-like way.
"""


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        max_tokens=300
    )

    return response.choices[0].message.content   # FIXED