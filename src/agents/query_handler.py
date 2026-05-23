"""Query Handler Agent — routes and preprocesses user requests."""
from src.agents.base_agent import BaseAgent
from src.core.config import config
from src.workflow.router import route_query


class QueryHandlerAgent(BaseAgent):
    """Routes requests to appropriate specialized agents and handles ambiguous queries."""

    def __init__(self):
        system_prompt = f"""You are {config['app']['name']}'s Query Handler.

Your role:
- Understand user intent and clarify ambiguous requests
- If the user's request is unclear, ask ONE clarifying question
- If clear, summarize what you'll do and which content types you'll create

Examples of clarification:
- "Write something about AI" → "Would you like a blog post, LinkedIn post, or both? Any specific angle?"
- "Content for my startup" → "What does your startup do? Who's your target audience?"

If the request is clear and specific, just confirm the plan briefly."""

        super().__init__(
            name="Query Handler Agent",
            system_prompt=system_prompt,
            tools=[],
        )
