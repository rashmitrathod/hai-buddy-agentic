"""
Agentic Orchestrator (Crew-style) — safe, explicit execution

This orchestrator preserves your CrewAI agent definitions (so the
demo can show agent roles, goals, and tools), but runs a deterministic
agentic pipeline by invoking the relevant tools in a controlled way.

Flow:
  1. Reasoner step (decide intent) — uses router.route_question() for robust routing
  2. Based on intent, run the corresponding tool:
       - course_rag  -> RAGRetrievalTool
       - code_help   -> CodeSearchTool
       - notes       -> SummaryTool
       - memory      -> MemoryTool
       - general_ai  -> direct LLM call (no retrieval)
  3. Buddy rewrite: final persona rewrite (Hinglish/English handling)
  4. Return final answer

This keeps CrewAI agents available (build_*_agent functions are still used to
construct the Agent objects for demo purposes), but avoids relying on an
uncertain Crew runtime in Cloud Run.
"""

from typing import Tuple
import traceback
import threading
import time
import os

from openai import OpenAI
from dotenv import load_dotenv

# keep the agent builders for demo visibility
from backend.services.crew.retriever_agent import build_retriever_agent
from backend.services.crew.reasoner_agent import build_reasoner_agent
from backend.services.crew.buddy_agent import build_buddy_agent

# tools and router
from backend.services.agent_tools import (
    RAGRetrievalTool,
    CodeSearchTool,
    SummaryTool,
    MemoryTool,
)
from backend.services.router import route_question

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Optional: configurable tool timeout in seconds (ensures no long blocking)
TOOL_TIMEOUT_SECONDS = int(os.getenv("TOOL_TIMEOUT_SECONDS", "12"))


class CrewOrchestrator:
    """
    Orchestrator that demonstrates Agentic pattern while executing tools
    deterministically and safely.
    """

    def __init__(self):
        # Build agent objects (for demo and metadata)
        try:
            self.retriever_agent = build_retriever_agent()
        except Exception:
            self.retriever_agent = None

        try:
            self.reasoner_agent = build_reasoner_agent()
        except Exception:
            self.reasoner_agent = None

        try:
            self.buddy_agent = build_buddy_agent()
        except Exception:
            self.buddy_agent = None

        # Keep instantiated tool objects if needed
        self.rag_tool = RAGRetrievalTool()
        self.code_tool = CodeSearchTool()
        self.notes_tool = SummaryTool()
        self.memory_tool = MemoryTool()

    # internal helper to call a tool with timeout
    def _run_tool_with_timeout(self, tool_callable, arg: str) -> str:
        """
        Run tool_callable(arg) but enforce timeout to avoid app hangs.
        tool_callable should be a callable returning str.
        """

        result_container = {"result": None, "error": None}

        def target():
            try:
                result_container["result"] = tool_callable(arg)
            except Exception as e:
                result_container["error"] = str(e) + "\n" + traceback.format_exc()

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(TOOL_TIMEOUT_SECONDS)

        if thread.is_alive():
            # tool timed out
            return f"[tool-timeout] The tool did not finish within {TOOL_TIMEOUT_SECONDS}s."
        if result_container["error"] is not None:
            return f"[tool-error] {result_container['error']}"
        return result_container["result"] or ""

    def _buddy_rewrite(self, question: str, intermediate_answer: str) -> str:
        """
        Rewrites the intermediate_answer using Buddy persona and Hinglish rules.
        """

        # The same persona template you used before; keep it concise
        system_prompt = f"""
You are HAI Buddy — a friendly male buddy who explains concepts in a casual, simple, and helpful way.
Keep responses short (2-3 sentences), warm, conversational, and never formal or academic.
If the user used Hinglish, reply naturally in Hinglish. Otherwise reply in English.
Use ONLY the intermediate answer below to rewrite; do not invent facts.
Intermediate answer:
{intermediate_answer}
User question:
{question}
Final rewritten answer:
"""
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=250
            )
            final = resp.choices[0].message.content.strip()
            return final
        except Exception as e:
            # never crash — return intermediate if LLM fails
            return intermediate_answer or f"[buddy-error] {str(e)}"

    def run(self, question: str) -> str:
        """
        Execute the agentic flow and return final answer (string).
        This method is safe for use on Cloud Run / SSE — it will always
        return a string and never hang indefinitely (tool timeouts).
        """

        try:
            # 1) Reasoner: call router to decide which tool to use
            # route_question returns (answer, intent)
            routed_answer, intent = route_question(question)
            # route_question itself may already run RAG or LLM for some intents.
            # We'll still interpret intent and (re)invoke the right tool to show delegation.
            # Log the decision (useful for demo)
            print(f"[Orchestrator] Reasoner routing result: intent={intent}")

            intermediate_answer = None

            # 2) Delegate to appropriate tool based on intent
            if intent in ("course_rag", "fallback"):
                print("[Orchestrator] Delegating to RAGRetrievalTool")
                intermediate_answer = self._run_tool_with_timeout(
                    lambda q: self.rag_tool._run(q), question
                )

            elif intent == "code_help":
                print("[Orchestrator] Delegating to CodeSearchTool")
                intermediate_answer = self._run_tool_with_timeout(
                    lambda q: self.code_tool._run(q), question
                )

            elif intent in ("notes", "notes_request"):
                print("[Orchestrator] Delegating to SummaryTool")
                intermediate_answer = self._run_tool_with_timeout(
                    lambda q: self.notes_tool._run(q), question
                )

            elif intent == "memory":
                print("[Orchestrator] Delegating to MemoryTool")
                intermediate_answer = self._run_tool_with_timeout(
                    lambda q: self.memory_tool._run(q), question
                )

            elif intent == "general_ai":
                # For general AI, route_question already returned an LLM-based answer in `routed_answer`
                # but we call a direct LLM as a "tool" to make delegation explicit in logs.
                print("[Orchestrator] Delegating to general LLM (direct)")
                intermediate_answer = self._run_tool_with_timeout(
                    lambda q: route_question(q)[0], question
                )

            else:
                # Fallback: use route_question's returned answer, but also attempt RAG
                print("[Orchestrator] Unknown intent — using routed answer and falling back to RAG")
                intermediate_answer = routed_answer or self._run_tool_with_timeout(
                    lambda q: self.rag_tool._run(q), question
                )

            # Ensure we have some reply
            if not intermediate_answer:
                intermediate_answer = "Sorry, I couldn't find information to answer that."

            # 3) Buddy rewrite (persona)
            final_answer = self._buddy_rewrite(question, intermediate_answer)

            # 4) Return final answer
            return final_answer

        except Exception as exc:
            print("[Orchestrator] Fatal error:", exc, traceback.format_exc())
            # Safe fallback text
            return f"Sorry — the orchestrator encountered an error: {str(exc)}"