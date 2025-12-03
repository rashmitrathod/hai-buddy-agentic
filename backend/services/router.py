from backend.services.intent_classifier import classify_intent
from backend.services.rag_engine import answer_with_rag
from backend.services.code_helper import answer_code_question
from backend.services.summary_service import generate_summary_for_question
from backend.services.memory_store import recall_memory
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def route_question(question: str) -> tuple[str, str]:
    """
    Accepts question and returns:
    (answer_text, intent)
    """

    intent = classify_intent(question)

    # 1) COURSE RAG
    if intent == "course_rag":
        answer = answer_with_rag(question)
        return answer, intent

    # 2) GENERAL AI KNOWLEDGE
    if intent == "general_ai":
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Be a friendly, helpful HAI Buddy."},
                {"role": "user", "content": question}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content, intent

    # 3) CODE HELP
    if intent == "code_help":
        answer = answer_code_question(question)
        return answer, intent

    # 4) NOTES / SUMMARIES
    if intent == "notes":
        answer = generate_summary_for_question(question)
        return answer, intent

    # 5) MEMORY
    if intent == "memory":
        answer = recall_memory(question)
        return answer, intent

    # FALLBACK
    fallback = f"I think you're asking about your course. Here's what I found:\n\n{answer_with_rag(question)}"
    return fallback, "fallback"