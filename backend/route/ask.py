# import os
# from fastapi import APIRouter, Request
# from backend.services.gcs_loader import list_transcripts, load_transcript
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv(override=True)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# router = APIRouter()

# @router.post("/ask")
# async def ask_question(request: Request):
#     """
#     Ask a question based on summaries stored in GCS.
#     """
#     body = await request.json()
#     question = body.get("question", "").strip()

#     if not question:
#         return {"error": "No question provided"}

#     bucket = os.getenv("GCS_BUCKET")
#     prefix = "summaries/"

#     # Load all summaries
#     blobs = list_transcripts(bucket, prefix)
#     summaries_text = []

#     for blob in blobs:
#         text = load_transcript(bucket, blob.name)
#         if text.strip():
#             summaries_text.append(text.strip())

#     if not summaries_text:
#         return {"error": "No summaries available to answer the question"}

#     # Combine summaries into context
#     context = "\n\n".join(summaries_text)

#     # Create the prompt for OpenAI
#     prompt = f"Answer the question based on the following summaries:\n\n{context}\n\nQuestion: {question}\nAnswer:"

#     # Call OpenAI Chat API
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "You are a helpful AI assistant."},
#             {"role": "user", "content": prompt}
#         ]
#     )

#     answer = response.choices[0].message.content.strip()

#     return {
#         "question": question,
#         "answer": answer
#     }