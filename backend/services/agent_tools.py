from crewai_tools import BaseTool

from backend.services.rag_engine import answer_with_rag
from backend.services.code_helper import answer_code_question
from backend.services.summary_service import generate_summary_for_question
from backend.services.memory_store import recall_memory


# 1) RAG TOOL ----------------------------------------------------

class RAGRetrievalTool(BaseTool):
    name: str = "rag_retrieval"
    description: str = (
        "Retrieve relevant transcript chunks from Udemy course using RAG and answer the question."
    )

    def _run(self, query: str) -> str:
        return answer_with_rag(query)


# 2) CODE HELP TOOL ----------------------------------------------

class CodeSearchTool(BaseTool):
    name: str = "code_helper"
    description: str = (
        "Provide programming/code explanations or debugging assistance."
    )

    def _run(self, query: str) -> str:
        return answer_code_question(query)


# 3) SUMMARY / NOTES TOOL ----------------------------------------

class SummaryTool(BaseTool):
    name: str = "notes_generator"
    description: str = (
        "Generate study notes or summaries for a given course question."
    )

    def _run(self, query: str) -> str:
        return generate_summary_for_question(query)


# 4) MEMORY TOOL -------------------------------------------------

class MemoryTool(BaseTool):
    name: str = "memory_recall"
    description: str = (
        "Recall previously discussed information or memory-based responses."
    )

    def _run(self, query: str) -> str:
        return recall_memory(query)


# 5) WEB SEARCH TOOL (placeholder for now) ------------------------

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Fetch general-purpose answers for installation steps, comparisons, tutorials, etc."
        " Placeholder implementation until actual SERP API is added."
    )

    def _run(self, query: str) -> str:
        # Placeholder — will replace later with SERP API or custom search
        return (
            "Web search tool placeholder: I don't have internet access yet, "
            "but soon I will be able to fetch external information."
        )