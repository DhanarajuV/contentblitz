"""Tests for the base agent class."""
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base_agent import BaseAgent


class TestBaseAgent:
    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_init_without_tools(self, mock_llm_class):
        agent = BaseAgent(name="Test", system_prompt="Test prompt")
        assert agent.name == "Test"
        assert agent.tools == []

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_init_with_tools(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = MagicMock()
        mock_llm_class.return_value = mock_llm

        from langchain_core.tools import tool

        @tool
        def dummy(x: str) -> str:
            """Dummy."""
            return x

        agent = BaseAgent(name="Test", system_prompt="Test", tools=[dummy])
        assert len(agent.tools) == 1
        mock_llm.bind_tools.assert_called_once()

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_run_returns_tuple(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        agent = BaseAgent(name="Test", system_prompt="Test")
        response, history = agent.run("Hello")
        assert response == "Hello response"
        assert len(history) == 2
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_run_handles_list_content(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "List response"}]
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        agent = BaseAgent(name="Test", system_prompt="Test")
        response, _ = agent.run("Hello")
        assert response == "List response"

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_run_handles_none_history(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        agent = BaseAgent(name="Test", system_prompt="Test")
        response, history = agent.run("Hello", None)
        assert response == "Response"
        assert len(history) == 2

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_run_preserves_history(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        agent = BaseAgent(name="Test", system_prompt="Test")
        existing = [HumanMessage(content="prev"), AIMessage(content="prev_ans")]
        _, history = agent.run("New", existing)
        assert len(history) == 4

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_tool_loop_executes(self, mock_llm_class):
        mock_llm = MagicMock()

        first = MagicMock()
        first.content = ""
        first.tool_calls = [{"name": "dummy", "args": {"x": "test"}, "id": "1"}]

        second = MagicMock()
        second.content = "Final"
        second.tool_calls = []

        mock_llm.invoke.side_effect = [first, second]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm_class.return_value = mock_llm

        from langchain_core.tools import tool

        @tool
        def dummy(x: str) -> str:
            """Dummy."""
            return f"Result: {x}"

        agent = BaseAgent(name="Test", system_prompt="Test", tools=[dummy])
        response, _ = agent.run("Use tool")
        assert response == "Final"
        assert mock_llm.invoke.call_count == 2

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_tool_loop_max_iterations(self, mock_llm_class):
        """Ensure tool loop doesn't run forever."""
        mock_llm = MagicMock()

        # Always return tool calls
        looping_response = MagicMock()
        looping_response.content = ""
        looping_response.tool_calls = [{"name": "dummy", "args": {"x": "t"}, "id": "1"}]

        final = MagicMock()
        final.content = "Done"
        final.tool_calls = []

        # 5 tool calls then final
        mock_llm.invoke.side_effect = [looping_response] * 5 + [final]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm_class.return_value = mock_llm

        from langchain_core.tools import tool

        @tool
        def dummy(x: str) -> str:
            """Dummy."""
            return "r"

        agent = BaseAgent(name="Test", system_prompt="Test", tools=[dummy])
        response, _ = agent.run("Loop")
        assert mock_llm.invoke.call_count == 6  # 5 tool rounds + 1 initial
