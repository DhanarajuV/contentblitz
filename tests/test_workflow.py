"""Tests for the workflow graph."""
from unittest.mock import patch, MagicMock
from src.workflow.graph import AGENT_PRIORITY, chat


class TestAgentPriority:
    def test_research_runs_first(self):
        assert AGENT_PRIORITY["research"] == 1

    def test_image_runs_last(self):
        assert AGENT_PRIORITY["image"] == max(AGENT_PRIORITY.values())

    def test_research_before_blog(self):
        assert AGENT_PRIORITY["research"] < AGENT_PRIORITY["blog"]

    def test_blog_before_image(self):
        assert AGENT_PRIORITY["blog"] < AGENT_PRIORITY["image"]

    def test_strategy_before_blog(self):
        assert AGENT_PRIORITY["strategy"] < AGENT_PRIORITY["blog"]

    def test_all_agents_have_priority(self):
        for agent in ["research", "blog", "linkedin", "image", "strategy"]:
            assert agent in AGENT_PRIORITY


class TestChatFunction:
    @patch("src.workflow.graph.app")
    def test_returns_tuple_of_three(self, mock_app):
        mock_app.invoke.return_value = {
            "response": "Test response",
            "agent_types": ["blog"],
            "chat_history": [],
        }
        response, label, history = chat("Write a blog")
        assert response == "Test response"
        assert label == "blog"
        assert history == []

    @patch("src.workflow.graph.app")
    def test_multi_agent_label(self, mock_app):
        mock_app.invoke.return_value = {
            "response": "Combined",
            "agent_types": ["research", "blog"],
            "chat_history": [],
        }
        _, label, _ = chat("Research and blog")
        assert label == "research, blog"

    @patch("src.workflow.graph.app")
    def test_default_empty_history(self, mock_app):
        mock_app.invoke.return_value = {
            "response": "R",
            "agent_types": ["research"],
            "chat_history": [],
        }
        chat("Hello")
        call_args = mock_app.invoke.call_args[0][0]
        assert call_args["chat_history"] == []

    @patch("src.workflow.graph.app")
    def test_passes_existing_history(self, mock_app):
        mock_app.invoke.return_value = {
            "response": "R",
            "agent_types": ["research"],
            "chat_history": ["msg"],
        }
        chat("Hello", ["prev"])
        call_args = mock_app.invoke.call_args[0][0]
        assert call_args["chat_history"] == ["prev"]
