import os
from dotenv import load_dotenv
from openai import OpenAI

from backend.services.vector_store import get_collection, query_chunks
from backend.services.embedding_utils import get_single_embedding

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


from backend.services.language_utils import is_hinglish  # make sure this import exists

def generate_llm_answer(query: str, context: str):
    """
    Generates the final LLM answer using persona rules
    + Hinglish detection enforcement.
    """

    # 1. Your long system prompt (unchanged)
    system_prompt = f"""
You are HAI Buddy — a friendly male buddy who explains concepts in a casual, simple, and helpful way.
You explain things the way a smart friend would, not like a textbook.

Your communication style:
- Use simple, everyday language
- Keep answers short (2-3 sentences)
- Speak casually and warmly
- Use small examples when helpful
- Avoid academic or formal tone
- Prefer “Imagine…” / “Think of it like…” to explain concepts
- Never overload with details
- Do NOT use emojis, emoticons, or words like “smile”, “haha”, “buddy”, “friend”.
- Do NOT add encouragement phrases unless asked.
- Avoid extra fluff.

Language rules:
- If user speaks in Hinglish → reply ONLY in Hinglish (mix Hindi + English).
- If user speaks in English → reply ONLY in English.
- Match user's language exactly. Never switch unless user switches.

You ONLY use the transcript context below to answer.

=====================
Transcript Context:
{context}
=====================
"""

    # 2. Base messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "Use the transcript context above to answer concisely."},
        {"role": "user", "content": query}
    ]

    # 3. Hinglish override (CRITICAL: this must come last)
    if is_hinglish(query):
        print("It is HINGLISH")
        messages.append({
            "role": "system",
            "content": (
                "IMPORTANT: User is speaking Hinglish. "
                "Reply ONLY in Hinglish — 70% Hindi + 30% English. "
                "Use natural desi tone: e.g., 'Bhai, video 3 mein mainly yeh bataya tha…'. "
                "Do NOT reply in pure English."
            )
        })

    print(f"rag_engine.py, messages: {messages}")

    print(f"Invoking OpenAI now")

    # 4. Call OpenAI
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=messages,
    #     max_tokens=300
    # )

    # print(f"OpenAI invocation completed, Response received")
    # return response.choices[0].message.content

    # response = client.responses.create(
    # model="gpt-4o-mini",
    # input=messages,
    # max_output_tokens=300)

    # return response.output_text

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    input=messages,
    max_tokens=300)
    return response.choices[0].message.content


def answer_with_rag(question: str) -> str:
    """
    Full RAG pipeline:
    1. embed question
    2. retrieve chunks
    3. rerank (optional future step)
    4. generate final answer
    """

    # Step 1: embed question
    q_emb = get_single_embedding(question)

    # Step 2: retrieve top chunks
    docs = query_chunks(q_emb)
    if not docs:
        return "Sorry, I could not find relevant information in your course transcripts."

    # Step 3: combine top docs
    context = "\n\n".join(docs)

    # Step 4: generate final answer
    prompt = f"""
    Use the course transcript content below to answer the student's question.

    Question:
    {question}

    Relevant Transcript Content:
    {context}

    Answer clearly, concisely, and in friendly tone.
    """
    # response = client.responses.create(
    # model="gpt-4o-mini",
    # input=[
    #     {"role": "system", "content": "You are HAI Buddy, a friendly course assistant."},
    #     {"role": "user", "content": prompt}
    # ],
    # max_output_tokens=300)
    # return response.output_text

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are HAI Buddy, a friendly assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=300)
    return response.choices[0].message.content