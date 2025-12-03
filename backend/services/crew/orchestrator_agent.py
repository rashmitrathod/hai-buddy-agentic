from backend.services.crew.retriever_agent import build_retriever_agent
from backend.services.crew.reasoner_agent import build_reasoner_agent
from backend.services.crew.buddy_agent import build_buddy_agent

from backend.services.intent_classifier import classify_intent
from backend.services.agent_tools import RAGRetrievalTool
from backend.services.tool_router_tool import ToolRouterTool
from backend.services.rag_engine import answer_with_rag

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class CrewOrchestrator:

    def __init__(self):
        self.retriever = build_retriever_agent()
        self.reasoner = build_reasoner_agent()
        self.buddy = build_buddy_agent()

    def run(self, question: str) -> str:
        """
        3-stage Agentic pipeline:
        
        1) Reasoner decides intent + tool usage
        2) Retriever fetches transcript context when needed
        3) Buddy rewrites final answer in Friendly/Hinglish persona
        """

        # ---- Stage 1: classify intent ----
        intent = classify_intent(question)
        print(f"[Orchestrator] Detected intent: {intent}")

        # ---- Stage 2: retrieve course context (only if needed) ----

        intermediate_answer = None

        if intent == "course_rag":
            print("[Orchestrator] Running RAGRetrievalTool for transcript answer")
            tool = RAGRetrievalTool()
            intermediate_answer = tool.run(question)

        elif intent == "code_help":
            print("[Orchestrator] Running CodeSearchTool")
            from backend.services.agent_tools import CodeSearchTool
            tool = CodeSearchTool()
            intermediate_answer = tool.run(question)

        elif intent == "notes_request":
            print("[Orchestrator] Running NotesTool")
            from backend.services.agent_tools import NotesTool
            tool = NotesTool()
            intermediate_answer = tool.run(question)

        else:
            print("[Orchestrator] Running general AI reasoning via LLM")
            intermediate_answer = answer_with_rag(question)   # fallback

        # ---- Stage 3: final rewrite by Buddy ----
        final_prompt = f"""
        Rewrite the following answer in a friendly conversational tone.

        If the user used Hinglish, respond in Hinglish naturally.
        If the user used English, respond in relaxed English.

        User question:
        {question}

        Initial answer:
        {intermediate_answer}

        Final Answer:
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly HAI Buddy."},
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=250
        )

        final_answer = response.choices[0].message.content.strip()
        return final_answer