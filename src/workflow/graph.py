from typing import TypedDict
from langgraph.graph import StateGraph, END

from src.workflow.router import route_query
from src.agents.research_agent import ResearchAgent
from src.agents.blog_writer import BlogWriterAgent
from src.agents.linkedin_writer import LinkedInWriterAgent
from src.agents.image_agent import ImageAgent
from src.agents.content_strategist import ContentStrategistAgent
from src.utils.guardrails import validate_input, check_content_safety

class AgentState(TypedDict):
    user_message: str
    chat_history: list
    agent_types: list
    response: str


agents = {
    "research": ResearchAgent(),
    "blog": BlogWriterAgent(),
    "linkedin": LinkedInWriterAgent(),
    "image": ImageAgent(),
    "strategy": ContentStrategistAgent(),
}

AGENT_PRIORITY = {
    "research": 1,
    "strategy": 2,
    "blog": 3,
    "linkedin": 4,
    "image": 5,
}


def router_node(state: AgentState) -> dict:
    agent_types = route_query(state["user_message"])
    return {"agent_types": agent_types}


def agent_node(state: AgentState) -> dict:
    agent_types = sorted(state["agent_types"], key=lambda a: AGENT_PRIORITY.get(a, 99))
    responses = []
    history = state["chat_history"]
    accumulated_context = ""

    for agent_type in agent_types:
        agent = agents[agent_type]

        if accumulated_context:
            enriched_message = (
                f"{state['user_message']}\n\n"
                f"Context from previous steps:\n{accumulated_context}"
            )
        else:
            enriched_message = state["user_message"]

        response, history = agent.run(enriched_message, history)
        responses.append(f"**[{agent.name}]**\n\n{response}")
        accumulated_context += f"\n{agent.name}: {response[:500]}\n"

    combined = "\n\n---\n\n".join(responses)
    return {"response": combined, "chat_history": history}


workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("router")
workflow.add_edge("router", "agent")
workflow.add_edge("agent", END)

app = workflow.compile()


def chat(user_message: str, chat_history: list = None) -> tuple[str, str, list]:
    if chat_history is None:
        chat_history = []

    # Input validation
    is_valid, error = validate_input(user_message)
    if not is_valid:
        return f"⚠️ {error}", "guardrail", chat_history

    # Input safety check
    is_safe, reason = check_content_safety(user_message)
    if not is_safe:
        return f"⚠️ {reason}", "guardrail", chat_history

    result = app.invoke({
        "user_message": user_message,
        "chat_history": chat_history,
        "agent_types": [],
        "response": "",
    })

    # Output safety check
    is_safe, reason = check_content_safety(result["response"])
    if not is_safe:
        print(f"DEBUG guardrail: {reason}")  # logs the matched word
        return f"⚠️ Content was filtered for safety. Please try a different topic.", "guardrail", chat_history

    agent_label = ", ".join(result["agent_types"])
    return result["response"], agent_label, result["chat_history"]
