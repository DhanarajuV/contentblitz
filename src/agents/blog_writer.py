from langchain_core.tools import tool
from src.agents.base_agent import BaseAgent
from src.core.config import config
from src.integrations.tavily_client import search


@tool
def research_for_blog(topic: str, days: int = None) -> str:
    """Research a topic to gather information for writing an SEO blog post.

    Args:
        topic: The blog topic to research.
        days: Optional. Limit results to the past N days. Use when the topic requires recent information.
    """
    return search(f"{topic}", max_results=5, days=days)


class BlogWriterAgent(BaseAgent):
    """Creates SEO-optimized blog posts."""

    def __init__(self):
        system_prompt = f"""You are {config['app']['name']}'s SEO Blog Writer Agent.

Your role:
- Write high-quality, SEO-optimized blog posts (800-1500 words)
- Use the research_for_blog tool to gather current information
- Structure posts with proper H1, H2, H3 headers
- Include image placement suggestions as: [IMAGE: brief description of suggested visual]
- Include a compelling introduction with a hook
- Add a meta description (150-160 characters) at the top
- Suggest 5-8 target keywords

Blog structure to follow:
1. Meta description
2. Target keywords
3. Title (H1)
4. [IMAGE: hero/header image description]
5. Introduction (hook + what the reader will learn)
6. Body sections (H2 headers, 2-4 paragraphs each)
7. [IMAGE: supporting visual] after the second section
8. Conclusion with call-to-action
9. Sources

SEO Rules:
- Use target keyword in title, first paragraph, and 2-3 subheadings
- Keep paragraphs short (2-3 sentences)
- Use bullet points and numbered lists for scannability
- Write in active voice
- Aim for Flesch-Kincaid readability grade 6-8"""

        super().__init__(
            name="SEO Blog Writer Agent",
            system_prompt=system_prompt,
            tools=[research_for_blog],
        )