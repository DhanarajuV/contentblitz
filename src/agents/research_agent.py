from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent
from src.core.config import config
from src.integrations.tavily_client import search


@tool
def web_research(query: str, days: int = None) -> str:
    """Conduct web research on a topic. Returns relevant articles with sources.

    Args:
        query: The research topic or question to search for.
        days: Optional. Limit results to the past N days. Use when the user asks for recent/latest information.
    """
    return search(query, max_results=config["research"]["max_results"], days=days)


class ResearchAgent(BaseAgent):
    """Conducts deep web research and provides comprehensive analysis."""

    def __init__(self):
        system_prompt = f"""You are {config['app']['name']}'s Deep Research Agent.

Your role:
- Conduct thorough web research using the web_research tool
- Synthesize findings into a clear, well-structured research summary
- Always cite sources with URLs
- Identify key trends, statistics, and expert opinions
- Organize research into sections: Key Findings, Trends, Statistics, Sources

Rules:
- ALWAYS use the web_research tool — never make up facts
- Cite every claim with its source URL
- Present information objectively
- Highlight conflicting viewpoints when they exist
- Format output in clean markdown with headers and bullet points"""

        super().__init__(
            name="Deep Research Agent",
            system_prompt=system_prompt,
            tools=[web_research],
        )