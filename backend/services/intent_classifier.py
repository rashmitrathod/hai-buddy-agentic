from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_intent(question: str) -> str:
    """
    Very lightweight intent classifier using GPT.
    Returns:
      - "course_rag"
      - "general_ai"
      - "code_help"
      - "web_search"
      - "notes"
      - "memory"
    """

    prompt = f"""
    Classify the user question into one intent category.

    Categories:
    - course_rag: Questions about Udemy course, videos, transcripts, agent demos.
    - general_ai: General AI / LLM / ML concepts not specific to the course.
    - code_help: Explaining or fixing code, programming, workflows.
    - web_search: Installation steps, comparisons, tutorials, external info.
    - notes: asking for notes, summaries, study material.
    - memory: asking about earlier conversation context.

    Respond ONLY with the intent name.

    User question: "{question}"
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a precise classifier."},
                  {"role": "user", "content": prompt}],
        max_tokens=10
    )

    intent = response.choices[0].message.content.strip().lower()

    # Safety fallback
    if intent not in ["course_rag", "general_ai", "code_help", "web_search", "notes", "memory"]:
        intent = "course_rag"

    return intent