"""Tests for the router module."""
from unittest.mock import patch, MagicMock
from src.workflow.router import route_query, AGENT_TYPES


class TestRouter:
    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_routes_research(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="research")
        mock_llm_class.return_value = mock_llm
        assert route_query("Research AI trends") == ["research"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_routes_blog(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="blog")
        mock_llm_class.return_value = mock_llm
        assert route_query("Write a blog post") == ["blog"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_routes_linkedin(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="linkedin")
        mock_llm_class.return_value = mock_llm
        assert route_query("Write a LinkedIn post") == ["linkedin"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_routes_image(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="image")
        mock_llm_class.return_value = mock_llm
        assert route_query("Generate an image") == ["image"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_routes_strategy(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="strategy")
        mock_llm_class.return_value = mock_llm
        assert route_query("Create a content strategy") == ["strategy"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_multi_agent_routing(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="research,blog,linkedin")
        mock_llm_class.return_value = mock_llm
        result = route_query("Full content package")
        assert "research" in result
        assert "blog" in result
        assert "linkedin" in result

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_fallback_on_invalid(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="invalid_thing")
        mock_llm_class.return_value = mock_llm
        assert route_query("random") == ["research"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_fallback_on_empty(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="")
        mock_llm_class.return_value = mock_llm
        assert route_query("hello") == ["research"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_strips_whitespace(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="  blog  ")
        mock_llm_class.return_value = mock_llm
        assert route_query("Write a blog") == ["blog"]

    @patch("src.workflow.router.ChatGoogleGenerativeAI")
    def test_handles_uppercase(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="BLOG")
        mock_llm_class.return_value = mock_llm
        assert route_query("Write a blog") == ["blog"]

    def test_agent_types_complete(self):
        assert AGENT_TYPES == ["research", "blog", "linkedin", "image", "strategy"]
