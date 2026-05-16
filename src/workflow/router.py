from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import config
from dotenv import load_dotenv

load_dotenv()

AGENT_TYPES = ["research", "blog", "linkedin", "image", "strategy"]

ROUTER_PROMPT = """You are a query router for a content marketing assistant.
Classify the user's message into one or more categories.

Categories:
- research: User wants to research a topic, find information, get data or insights
- blog: User wants to write a blog post, article, or long-form content
- linkedin: User wants to write a LinkedIn post or professional social media content
- image: User wants to generate an image, visual, or graphic
- strategy: User wants a content plan, content calendar, or advice on content approach

Rules:
- If the query involves MULTIPLE categories, return ALL that apply separated by commas
- "Write a blog post about X" → blog
- "Write a blog post with images about X" → blog,image
- "Write a complete blog about X" → blog,image
- "Research X and then write a blog" → research,blog
- "Create a full content package about X" → research,blog,linkedin,image
- If user says "with images", "with visuals", or "complete", always include image
- If unclear, default to research

Respond with ONLY the category name(s), nothing else."""


def route_query(user_message: str) -> list[str]:
    """Classify a user message. Returns list of agent types."""
    llm = ChatGoogleGenerativeAI(model=config["llm"]["model"], temperature=0)

    response = llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=user_message),
    ])

    raw = response.content.strip().lower()
    agent_types = [a.strip() for a in raw.split(",")]
    valid = [a for a in agent_types if a in AGENT_TYPES]

    return valid if valid else ["research"]


if __name__ == "__main__":
    tests = [
        "Research the latest AI trends",
        "Write a blog post about remote work",
        "Create a LinkedIn post about leadership",
        "Generate an image for my marketing campaign",
        "Create a content strategy for my SaaS startup",
        "Research AI trends and write a blog and LinkedIn post about it",
    ]

    for q in tests:
        result = route_query(q)
        print(f"{str(result):50s} ← {q}")