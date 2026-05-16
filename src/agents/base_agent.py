import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from src.core.config import config

load_dotenv()


class BaseAgent:
    """Base class for all ContentBlitz agents."""

    def __init__(self, name: str, system_prompt: str, tools: list = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []

        self.llm = ChatGoogleGenerativeAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
        )

        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

    def run(self, user_message: str, chat_history: list = None) -> tuple[str, list]:
        """Process a user message. Returns (response_text, updated_history)."""
        if chat_history is None:
            chat_history = []

        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_message))

        # Loop until LLM stops requesting tools (max 5 iterations to prevent infinite loops)
        response = self.llm_with_tools.invoke(messages)
        iterations = 0

        while response.tool_calls and iterations < 5:
            messages.append(response)
            tool_map = {t.name: t for t in self.tools}

            for tool_call in response.tool_calls:
                func = tool_map[tool_call["name"]]
                result = func.invoke(tool_call["args"])
                messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

            response = self.llm_with_tools.invoke(messages)
            iterations += 1

        content = response.content
        if isinstance(content, list):
            content = "".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )

        chat_history.append(HumanMessage(content=user_message))
        chat_history.append(AIMessage(content=content))

        return content, chat_history