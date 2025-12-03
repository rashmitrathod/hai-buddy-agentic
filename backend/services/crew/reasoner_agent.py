from crewai import Agent
from backend.services.tool_router_tool import ToolRouterTool

def build_reasoner_agent():
    return Agent(
        role="Reasoning Specialist",
        goal="Select the right tool, analyze the information, and produce a correct intermediate answer.",
        backstory="You are an expert at deciding which tool or retrieval method to use.",
        verbose=True,
        allow_delegation=True,
        tools=[ToolRouterTool()]   # key tool
    )