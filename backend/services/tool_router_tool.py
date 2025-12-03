from crewai.tools import BaseTool
from pydantic import Field
from typing import Optional

from backend.services.router import route_question

class ToolRouterTool(BaseTool):
    """
    A CrewAI tool that routes the question to the correct subtool
    based on intent (RAG, code help, notes, general AI, memory, etc.)
    """

    name: str = "tool_router"
    description: str = (
        "Smart tool router that decides which tool to use based on the user's intent "
        "(course RAG, code help, summaries, general AI, memory, or web search)."
    )

    def _run(self, query: str) -> str:
        answer, intent = route_question(query)
        return f"[intent={intent}] {answer}"