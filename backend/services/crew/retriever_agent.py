from crewai import Agent
from backend.services.agent_tools import RAGRetrievalTool

def build_retriever_agent():
    return Agent(
        role="RAG Retriever",
        goal="Retrieve the most relevant transcript chunks for the user's question.",
        backstory="You specialize in searching course transcripts using RAG.",
        verbose=True,
        allow_delegation=False,
        tools=[RAGRetrievalTool()]   # attach tool
    )